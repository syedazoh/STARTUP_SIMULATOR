"""Durable, business-scoped boardroom activity. Only observed actions are recorded.

These records are visual/audit projections, not commands and never approve work.
"""
from datetime import datetime, timezone
from uuid import uuid4
import re
import logging

AGENTS = {"ceo", "finance", "marketing", "hr", "operations", "strategy"}
RECEIVERS = {
    "budget_request": "finance",
    "budget_negotiation": "marketing",
    "campaign_launch": "marketing",
    "recruitment_request": "hr",
    "resource_request": "operations",
    "arbitration_request": "ceo",
    "arbitration_result": "finance",
}

def normalize_agent(value):
    if not isinstance(value, str):
        return None
    name = value.lower()
    if name in AGENTS:
        return name
    for agent in AGENTS:
        suffix = name.removeprefix(agent + "_")
        if name.startswith(agent + "_") and (
            suffix == "agent" or suffix.isdigit() or
            re.fullmatch(r"[a-f0-9]{24}|[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", suffix)
        ):
            return agent
    return None

def infer_internal_route(source, event_type):
    """Only agent-originated events routed to a subscribed department."""
    sender = normalize_agent(source)
    receiver = RECEIVERS.get(event_type)
    if not sender or not receiver or sender == receiver:
        return None
    return sender, receiver

async def record_handoff(db, business_id, sender, receiver, event_type, title,
                         task_id=None, plan_id=None, event_id=None):
    if sender not in AGENTS or receiver not in AGENTS or sender == receiver:
        raise ValueError("Handoff requires two distinct known agents")
    event = {
        "event_id": event_id or str(uuid4()),
        "business_id": business_id,
        "event_type": event_type,
        "source": sender,
        "sender": sender,
        "receiver": receiver,
        "data": {
            "title": str(title or event_type)[:200],
            **({"task_id": task_id} if task_id else {}),
            **({"plan_id": plan_id} if plan_id else {}),
        },
        "timestamp": datetime.now(timezone.utc),
    }
    await db["collaboration_events"].insert_one(event)
    return event["event_id"]

async def record_decision_activity(db, business_id, decision_type, run_id=None,
                                   tick=None, task_id=None):
    await db["collaboration_events"].insert_one({
        "event_id": str(uuid4()),
        "business_id": business_id,
        "event_type": "decision_recorded",
        "source": "system",
        "data": {
            "title": "Decision recorded: " + str(decision_type).replace("_", " "),
            "decision_type": decision_type,
            "run_id": run_id,
            "tick": tick,
            "task_id": task_id,
        },
        "timestamp": datetime.now(timezone.utc),
    })

async def list_collaboration_events(db, business_id, limit=100):
    docs = await db["collaboration_events"].find(
        {"business_id": business_id}
    ).sort("timestamp", -1).to_list(length=min(max(limit, 1), 200))
    result = []
    for doc in reversed(docs):
        result.append({
            key: (value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value).isoformat() if isinstance(value, datetime) else value
            for key, value in doc.items() if key not in {"_id", "business_id"}
        })
    return result

async def best_effort_handoff(*args, **kwargs):
    """A failed visual projection must never invalidate an actual task or approval."""
    try:
        await record_handoff(*args, **kwargs)
    except Exception:
        logging.getLogger(__name__).exception("Could not record boardroom handoff")

async def best_effort_decision_activity(*args, **kwargs):
    try:
        await record_decision_activity(*args, **kwargs)
    except Exception:
        logging.getLogger(__name__).exception("Could not record boardroom decision activity")
