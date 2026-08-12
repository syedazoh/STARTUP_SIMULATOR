"""Event routes (business-scoped)"""
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from ..deps import get_owned_business
from ...models.business_schemas import BusinessOut

router = APIRouter(prefix="/api/businesses/{business_id}/events", tags=["events"])


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


@router.post("")
async def publish_event(
    payload: PublishEventRequest, request: Request, business: BusinessOut = Depends(get_owned_business)
):
    runtime = await request.app.state.agent_registry.get_or_create(business)
    await runtime.agent_manager.process_event(payload.event_type, payload.data, source=payload.source)
    return {"status": "published", "event_type": payload.event_type}
