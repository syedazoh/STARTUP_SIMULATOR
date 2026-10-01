"""Agent automation policy routes (business-scoped)"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from ..deps import get_owned_business
from ...core.rate_limit import RateLimiter, rate_limit_dependency
from ...database.utils import find_one
from ...models.business_schemas import BusinessOut
from ...models.policy_schemas import AgentPolicyIn, AgentPolicyOut

router = APIRouter(prefix="/api/businesses/{business_id}/agents/{agent_key}/policy", tags=["policies"])

_policy_rate_limiter = RateLimiter(max_requests=30, window_seconds=60)
_rate_limited = Depends(rate_limit_dependency(_policy_rate_limiter))

# CEO arbitration is system-triggered by Finance's escalation path, not a
# user-initiated department action — it doesn't fit the threshold-policy shape.
DEPARTMENT_AGENT_KEYS = {"finance", "marketing", "hr", "operations"}


def _to_policy_out(doc: dict) -> AgentPolicyOut:
    return AgentPolicyOut(
        enabled=doc.get("enabled", False),
        auto_approve_max=doc.get("auto_approve_max"),
        auto_deny_min=doc.get("auto_deny_min"),
        updated_at=doc["updated_at"],
    )


@router.get("", response_model=AgentPolicyOut)
async def get_policy(agent_key: str, request: Request, business: BusinessOut = Depends(get_owned_business)):
    if agent_key not in DEPARTMENT_AGENT_KEYS:
        raise HTTPException(status_code=404, detail=f"No policy for agent: {agent_key}")

    doc = await find_one(
        request.app.state.db["agent_policies"], {"business_id": business.id, "agent_key": agent_key}
    )
    if doc is None:
        return AgentPolicyOut(
            enabled=False, auto_approve_max=None, auto_deny_min=None, updated_at=datetime.now(timezone.utc)
        )
    return _to_policy_out(doc)


@router.put("", response_model=AgentPolicyOut, dependencies=[_rate_limited])
async def update_policy(
    agent_key: str,
    payload: AgentPolicyIn,
    request: Request,
    business: BusinessOut = Depends(get_owned_business),
):
    if agent_key not in DEPARTMENT_AGENT_KEYS:
        raise HTTPException(status_code=404, detail=f"No policy for agent: {agent_key}")

    db = request.app.state.db
    updated_at = datetime.now(timezone.utc)
    doc = {
        "business_id": business.id,
        "agent_key": agent_key,
        "enabled": payload.enabled,
        "auto_approve_max": payload.auto_approve_max,
        "auto_deny_min": payload.auto_deny_min,
        "updated_at": updated_at,
    }

    existing = await find_one(db["agent_policies"], {"business_id": business.id, "agent_key": agent_key})
    if existing is None:
        await db["agent_policies"].insert_one(doc)
    else:
        await db["agent_policies"].update_one(
            {"business_id": business.id, "agent_key": agent_key}, {"$set": doc}
        )

    # Apply immediately to the live in-memory agent — no restart needed.
    runtime = await request.app.state.agent_registry.get_or_create(business)
    agent = runtime.agent_manager.agents.get(agent_key)
    if agent is not None:
        agent.set_policy(_to_policy_out(doc))

    return _to_policy_out(doc)
