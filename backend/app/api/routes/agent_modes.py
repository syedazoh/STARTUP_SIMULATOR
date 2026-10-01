"""Agent execution mode routes (business-scoped): manual vs auto.

Mirrors policies.py's upsert shape and its DEPARTMENT_AGENT_KEYS restriction
(imported rather than redefined) — CEO arbitration has no user-triggered
action to gate, so it gets no mode either.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from ..deps import get_owned_business
from ...core.rate_limit import RateLimiter, rate_limit_dependency
from ...database.utils import find_one
from ...models.agent_mode_schemas import AgentModeIn, AgentModeOut
from ...models.business_schemas import BusinessOut
from .policies import DEPARTMENT_AGENT_KEYS

router = APIRouter(prefix="/api/businesses/{business_id}/agents/{agent_key}/mode", tags=["agent_modes"])

_mode_rate_limiter = RateLimiter(max_requests=30, window_seconds=60)
_rate_limited = Depends(rate_limit_dependency(_mode_rate_limiter))


def _to_mode_out(doc: dict) -> AgentModeOut:
    return AgentModeOut(
        mode=doc.get("mode", "manual"),
        auto_thresholds=doc.get("auto_thresholds", {}),
        updated_at=doc["updated_at"],
    )


@router.get("", response_model=AgentModeOut)
async def get_mode(agent_key: str, request: Request, business: BusinessOut = Depends(get_owned_business)):
    if agent_key not in DEPARTMENT_AGENT_KEYS:
        raise HTTPException(status_code=404, detail=f"No mode for agent: {agent_key}")

    doc = await find_one(request.app.state.db["agent_modes"], {"business_id": business.id, "agent": agent_key})
    if doc is None:
        return AgentModeOut(mode="manual", auto_thresholds={}, updated_at=datetime.now(timezone.utc))
    return _to_mode_out(doc)


@router.put("", response_model=AgentModeOut, dependencies=[_rate_limited])
async def update_mode(
    agent_key: str,
    payload: AgentModeIn,
    request: Request,
    business: BusinessOut = Depends(get_owned_business),
):
    if agent_key not in DEPARTMENT_AGENT_KEYS:
        raise HTTPException(status_code=404, detail=f"No mode for agent: {agent_key}")

    db = request.app.state.db
    updated_at = datetime.now(timezone.utc)
    doc = {
        "business_id": business.id,
        "agent": agent_key,
        "mode": payload.mode,
        "auto_thresholds": payload.auto_thresholds.model_dump(),
        "updated_at": updated_at,
    }

    existing = await find_one(db["agent_modes"], {"business_id": business.id, "agent": agent_key})
    if existing is None:
        await db["agent_modes"].insert_one(doc)
    else:
        await db["agent_modes"].update_one({"business_id": business.id, "agent": agent_key}, {"$set": doc})

    return _to_mode_out(doc)
