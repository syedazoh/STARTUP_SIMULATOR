"""Per-agent chat: free-form conversation with an agent, with the ability
to request an action as a side effect.

The LLM never executes anything — ChatReply only ever lets it *ask* for an
action, and send_message() is the only code that turns that into a real
create_task() call. That keeps chat-originated actions on the exact same
manual/auto/threshold pipeline every other entry point uses instead of a
parallel "the chatbot did it directly" path.
"""
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..agents.schemas import ChatReply
from ..core.llm import get_groq_llm
from ..database.utils import find_one
from ..models.business_schemas import BusinessOut
from .tasks import create_task

# Which action_types a chat message is allowed to request per agent, and the
# payload fields the LLM must fill in — mirrors the manual action endpoints
# in routes/agent_actions.py so chat can't invent an action_type nothing
# actually knows how to execute. CEO has no entry: arbitration is
# system-triggered, not something the owner asks for directly (same reason
# it has no manual action endpoint or policy).
AGENT_ACTIONS: Dict[str, Dict[str, List[str]]] = {
    "finance": {"budget_request": ["amount", "department"]},
    "marketing": {
        "campaign_launch": ["campaign_name", "requested_budget"],
        "instagram_post": ["content"],
        "reel_request": ["campaign_name", "brief"],
    },
    "hr": {"recruitment_request": ["role", "headcount"]},
    "operations": {"resource_request": ["resource_type", "quantity"]},
}

AGENT_PERSONAS = {
    "finance": "You are the Finance Manager of a startup: careful with money, direct, focused on runway.",
    "marketing": "You are the Marketing Manager of a startup: energetic, brand-focused, customer-obsessed.",
    "hr": "You are the HR Manager of a startup: people-focused, fair, mindful of team morale.",
    "operations": "You are the Operations Manager of a startup: pragmatic, focused on reliability and efficiency.",
    "ceo": "You are the CEO of a startup: strategic, and you arbitrate between departments when they conflict.",
}

MAX_HISTORY_MESSAGES = 20


def _empty_thread(business_id: str, agent: str) -> Dict[str, Any]:
    return {"business_id": business_id, "agent": agent, "messages": [], "updated_at": datetime.now(timezone.utc)}


async def get_thread(db, business_id: str, agent: str) -> Dict[str, Any]:
    doc = await find_one(db["chat_threads"], {"business_id": business_id, "agent": agent})
    return doc if doc is not None else _empty_thread(business_id, agent)


def _build_prompt(
    agent: str,
    profile: Optional[Dict[str, Any]],
    live_status: Optional[Dict[str, Any]],
    history: List[Dict[str, Any]],
    content: str,
) -> str:
    lines = [AGENT_PERSONAS.get(agent, "You are a helpful startup team member."), ""]

    if live_status:
        # Without this, the LLM has no grounding for questions like "how
        # much budget do we have" and will confidently make up a number —
        # this is the actual current state of the simulated business.
        lines.append(f"Your current status: {json.dumps(live_status, default=str)}")
        lines.append("Answer questions about numbers using this status, not a guess.")
        lines.append("")

    if profile:
        context = {k: v for k, v in profile.items() if k not in ("_id", "business_id", "updated_at")}
        if any(context.values()):
            lines.append(f"Business context: {json.dumps(context, default=str)}")
            lines.append("")

    actions = AGENT_ACTIONS.get(agent, {})
    if actions:
        action_desc = "; ".join(f'"{name}" (fields: {", ".join(fields)})' for name, fields in actions.items())
        lines.append(
            "If the owner's message asks you to actually take an action (not just answer a question), "
            f"set action_requested=true, action_type to exactly one of: {action_desc}, and "
            "action_payload_json to a JSON object (as a string) with exactly those fields. Otherwise leave "
            "those three fields empty and just reply conversationally."
        )
        lines.append("")

    if history:
        lines.append("Recent conversation:")
        for msg in history[-MAX_HISTORY_MESSAGES:]:
            lines.append(f"{msg['role']}: {msg['content']}")
        lines.append("")

    lines.append(f"owner: {content}")
    return "\n".join(lines)


async def send_message(db, agent_registry, business: BusinessOut, agent: str, content: str) -> Dict[str, Any]:
    thread = await get_thread(db, business.id, agent)
    profile = await find_one(db["business_profiles"], {"business_id": business.id})

    runtime = await agent_registry.get_or_create(business)
    live_agent = runtime.agent_manager.agents.get(agent)
    live_status = await live_agent.get_status() if live_agent is not None else None

    prompt = _build_prompt(agent, profile, live_status, thread["messages"], content)
    try:
        reply: ChatReply = await get_groq_llm().with_structured_output(ChatReply).ainvoke(prompt)
    except Exception:
        reply = ChatReply(reply="Sorry, I couldn't process that just now — could you try again?")

    now = datetime.now(timezone.utc)
    messages = thread["messages"] + [
        {"role": "owner", "content": content, "created_at": now},
        {"role": "agent", "content": reply.reply, "created_at": now},
    ]
    doc = {"business_id": business.id, "agent": agent, "messages": messages, "updated_at": now}

    existing = await find_one(db["chat_threads"], {"business_id": business.id, "agent": agent})
    if existing is None:
        await db["chat_threads"].insert_one(doc)
    else:
        await db["chat_threads"].update_one({"business_id": business.id, "agent": agent}, {"$set": doc})

    task = None
    allowed = AGENT_ACTIONS.get(agent, {})
    if reply.action_requested and reply.action_type in allowed:
        try:
            payload = json.loads(reply.action_payload_json or "{}")
        except (json.JSONDecodeError, TypeError):
            payload = None
        if isinstance(payload, dict):
            task = await create_task(db, agent_registry, business, agent, reply.action_type, payload)

    return {"thread": doc, "task": task}
