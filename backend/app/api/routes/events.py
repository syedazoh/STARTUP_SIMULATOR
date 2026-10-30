"""Event routes (business-scoped)"""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ValidationError

from ...models.action_schemas import ACTION_CONTRACTS
from ...core.rate_limit import RateLimiter, rate_limit_dependency
from ...services.tasks import create_task

from ..deps import get_owned_business
from ...models.business_schemas import BusinessOut

router = APIRouter(prefix="/api/businesses/{business_id}/events", tags=["events"])

# Event types a client is allowed to trigger directly — mirrors the
# user-initiated actions agent_actions.py and the simulation event generator
# already fire. Excludes agent-to-agent negotiation/arbitration events
# (budget_negotiation, arbitration_request, arbitration_result): those are
# only ever meant to be published by an agent reacting to another agent, so
# letting an external caller inject one directly would let it forge a step
# in that internal chain.
PUBLISHABLE_EVENT_TYPES = {
    "budget_request",
    "campaign_launch",
    "instagram_post",
    "reel_request",
    "recruitment_request",
    "resource_request",
}


class PublishEventRequest(BaseModel):
    event_type: str
    data: Dict[str, Any] = {}
    source: str = "api"


@router.get("")
async def list_events(
    request: Request, business: BusinessOut = Depends(get_owned_business), limit: int = 100
):
    runtime = await request.app.state.agent_registry.get_or_create(business)
    return runtime.agent_manager.event_bus.get_event_history(limit=limit)


_limiter = RateLimiter(max_requests=30, window_seconds=60)

@router.post("", dependencies=[Depends(rate_limit_dependency(_limiter))])
async def publish_event(
    payload: PublishEventRequest, request: Request, business: BusinessOut = Depends(get_owned_business)
):
    if payload.event_type not in PUBLISHABLE_EVENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Event type is not publishable: {payload.event_type}",
        )

    try:
        task = await create_task(
            request.app.state.db, request.app.state.agent_registry, business,
            ACTION_CONTRACTS[payload.event_type][0], payload.event_type, payload.data,
            source="api",
        )
    except (ValueError, ValidationError) as exc:
        raise HTTPException(status_code=422, detail="Invalid action payload") from exc
    return {"status": "queued", "event_type": payload.event_type, "task_id": task["task_id"]}
