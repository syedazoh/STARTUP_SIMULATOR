"""Manual per-agent action routes (business-scoped).

Each endpoint creates a task through the shared approval pipeline. Agent
effects run only after owner approval or an allowed automatic-mode decision.
"""
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from ..deps import get_owned_business
from ...core.rate_limit import RateLimiter, rate_limit_dependency
from ...models.business_schemas import BusinessOut
from ...models.task_schemas import TaskOut, to_task_out
from ...services.tasks import create_task

router = APIRouter(prefix="/api/businesses/{business_id}/agents", tags=["agent-actions"])

# All user-initiated actions share one task-creation rate limit.
_action_rate_limiter = RateLimiter(max_requests=30, window_seconds=60)
_rate_limited = Depends(rate_limit_dependency(_action_rate_limiter))


class BudgetRequestAction(BaseModel):
    amount: float
    department: str = "General"


class CampaignLaunchAction(BaseModel):
    campaign_name: str
    requested_budget: float = 5000


class InstagramPostAction(BaseModel):
    content: str


class ReelRequestAction(BaseModel):
    campaign_name: str
    brief: str = ""


class RecruitmentRequestAction(BaseModel):
    role: str
    headcount: int = 1


class ResourceRequestAction(BaseModel):
    resource_type: str
    quantity: int = 1


@router.post("/finance/actions/budget-request", response_model=TaskOut, dependencies=[_rate_limited])
async def finance_budget_request(
    payload: BudgetRequestAction, request: Request, business: BusinessOut = Depends(get_owned_business)
):
    task = await create_task(
        request.app.state.db,
        request.app.state.agent_registry,
        business,
        "finance",
        "budget_request",
        payload.model_dump(),
    )
    return to_task_out(task)


@router.post("/marketing/actions/campaign-launch", response_model=TaskOut, dependencies=[_rate_limited])
async def marketing_campaign_launch(
    payload: CampaignLaunchAction, request: Request, business: BusinessOut = Depends(get_owned_business)
):
    task = await create_task(
        request.app.state.db,
        request.app.state.agent_registry,
        business,
        "marketing",
        "campaign_launch",
        payload.model_dump(),
    )
    return to_task_out(task)


@router.post("/marketing/actions/instagram-post", response_model=TaskOut, dependencies=[_rate_limited])
async def marketing_instagram_post(
    payload: InstagramPostAction, request: Request, business: BusinessOut = Depends(get_owned_business)
):
    task = await create_task(
        request.app.state.db,
        request.app.state.agent_registry,
        business,
        "marketing",
        "instagram_post",
        payload.model_dump(),
    )
    return to_task_out(task)


@router.post("/marketing/actions/reel-request", response_model=TaskOut, dependencies=[_rate_limited])
async def marketing_reel_request(
    payload: ReelRequestAction, request: Request, business: BusinessOut = Depends(get_owned_business)
):
    task = await create_task(
        request.app.state.db,
        request.app.state.agent_registry,
        business,
        "marketing",
        "reel_request",
        payload.model_dump(),
        requires_asset=True,
    )
    return to_task_out(task)


@router.post("/hr/actions/recruitment-request", response_model=TaskOut, dependencies=[_rate_limited])
async def hr_recruitment_request(
    payload: RecruitmentRequestAction, request: Request, business: BusinessOut = Depends(get_owned_business)
):
    task = await create_task(
        request.app.state.db,
        request.app.state.agent_registry,
        business,
        "hr",
        "recruitment_request",
        payload.model_dump(),
    )
    return to_task_out(task)


@router.post("/operations/actions/resource-request", response_model=TaskOut, dependencies=[_rate_limited])
async def operations_resource_request(
    payload: ResourceRequestAction, request: Request, business: BusinessOut = Depends(get_owned_business)
):
    task = await create_task(
        request.app.state.db,
        request.app.state.agent_registry,
        business,
        "operations",
        "resource_request",
        payload.model_dump(),
    )
    return to_task_out(task)
