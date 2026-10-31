"""Per-agent chat routes (business-scoped)."""
from fastapi import APIRouter, Depends, HTTPException, Request

from ..deps import get_owned_business
from ...core.rate_limit import RateLimiter, rate_limit_dependency
from ...models.business_schemas import BusinessOut
from ...models.chat_schemas import ChatMessageIn, ChatReplyOut, ChatThreadOut
from ...models.task_schemas import to_task_out
from ...services.chat import get_thread, send_message

router = APIRouter(prefix="/api/businesses/{business_id}/agents/{agent_key}/chat", tags=["chat"])

# Chat is the most expensive endpoint in the app per call (a real LLM
# round-trip, sometimes two if it also creates a task) — capped tighter
# than task-creation endpoints.
_chat_rate_limiter = RateLimiter(max_requests=15, window_seconds=60)


async def _require_known_agent(request: Request, business: BusinessOut, agent_key: str) -> None:
    runtime = await request.app.state.agent_registry.get_or_create(business)
    if agent_key not in runtime.agent_manager.agents:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_key}")


@router.get("", response_model=ChatThreadOut)
async def get_chat_thread(agent_key: str, request: Request, business: BusinessOut = Depends(get_owned_business)):
    await _require_known_agent(request, business, agent_key)
    thread = await get_thread(request.app.state.db, business.id, agent_key)
    return ChatThreadOut(**thread)


@router.post("", response_model=ChatReplyOut, dependencies=[Depends(rate_limit_dependency(_chat_rate_limiter))])
async def post_chat_message(
    agent_key: str,
    payload: ChatMessageIn,
    request: Request,
    business: BusinessOut = Depends(get_owned_business),
):
    await _require_known_agent(request, business, agent_key)
    result = await send_message(
        request.app.state.db, request.app.state.agent_registry, business, agent_key, payload.content
    )
    return ChatReplyOut(
        thread=ChatThreadOut(**result["thread"]),
        ai_error=result.get("ai_error"),
        task=to_task_out(result["task"]) if result["task"] else None,
    )
