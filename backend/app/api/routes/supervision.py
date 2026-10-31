"""Owner-scoped CEO planning and departmental reporting API."""

from fastapi import APIRouter, Depends, Request
from ..deps import get_owned_business
from ...core.rate_limit import RateLimiter, rate_limit_dependency
from ...models.business_schemas import BusinessOut
from ...models.supervision_schemas import GoalIn
from ...services.supervision import propose_plan, activate_plan

router = APIRouter(prefix="/api/businesses/{business_id}/ceo", tags=["ceo"])
_limiter = RateLimiter(max_requests=10, window_seconds=60)
_limited = Depends(rate_limit_dependency(_limiter))


@router.post("/plans", dependencies=[_limited])
async def create_plan(
    payload: GoalIn,
    request: Request,
    business: BusinessOut = Depends(get_owned_business),
):
    return await propose_plan(
        request.app.state.db, request.app.state.agent_registry, business, payload.goal
    )


@router.post("/plans/{plan_id}/activate", dependencies=[_limited])
async def assign_plan(
    plan_id: str, request: Request, business: BusinessOut = Depends(get_owned_business)
):
    return await activate_plan(
        request.app.state.db, request.app.state.agent_registry, business, plan_id
    )


async def _list(request, business, collection):
    docs = (
        await request.app.state.db[collection]
        .find({"business_id": business.id})
        .sort("created_at", -1)
        .to_list(length=100)
    )
    return [{k: v for k, v in doc.items() if k != "_id"} for doc in docs]


@router.get("/plans")
async def plans(request: Request, business: BusinessOut = Depends(get_owned_business)):
    return await _list(request, business, "ceo_plans")


@router.get("/reports")
async def reports(
    request: Request, business: BusinessOut = Depends(get_owned_business)
):
    from ...services.supervision import schedule_pending_reviews

    runtime = await request.app.state.agent_registry.get_or_create(business)
    await schedule_pending_reviews(request.app.state.db, business, runtime)
    return await _list(request, business, "department_reports")
