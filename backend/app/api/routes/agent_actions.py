"""Manual per-agent action routes (business-scoped).

Each endpoint fires the same event contract each agent already handles when
reacting to a simulation tick — no new event types, just a user-initiated
entry point instead of the synthetic event generator.

Finance's budget-request endpoint is the Phase 2 reference implementation of
the task/approval pipeline: it goes through create_task() instead of firing
straight into the agent, so it can land as pending_approval instead of
executing immediately when Finance is in manual mode. The other three
endpoints still call the agent directly — they're next in line to be wired
through the same pipeline, not intentionally left out.
"""
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from ..deps import get_owned_business
from ...models.business_schemas import BusinessOut
from ...models.task_schemas import TaskOut, to_task_out
from ...services.persistence import record_decision, snapshot_agents
from ...services.tasks import create_task

router = APIRouter(prefix="/api/businesses/{business_id}/agents", tags=["agent-actions"])


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


async def _trigger_and_record(
    request: Request, business: BusinessOut, agent_key: str, event_type: str, data: dict
):
    runtime = request.app.state.agent_registry.get_or_create(business)
    result = await runtime.agent_manager.trigger_action(agent_key, event_type, data)

    db = request.app.state.db
    await record_decision(db, business.id, event_type, data, source="manual")
    await snapshot_agents(db, business.id, runtime.agent_manager)

    return result


@router.post("/finance/actions/budget-request", response_model=TaskOut)
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


@router.post("/marketing/actions/campaign-launch")
async def marketing_campaign_launch(
    payload: CampaignLaunchAction, request: Request, business: BusinessOut = Depends(get_owned_business)
):
    return await _trigger_and_record(
        request, business, "marketing", "campaign_launch", payload.model_dump()
    )


@router.post("/marketing/actions/instagram-post", response_model=TaskOut)
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


@router.post("/marketing/actions/reel-request", response_model=TaskOut)
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


@router.post("/hr/actions/recruitment-request")
async def hr_recruitment_request(
    payload: RecruitmentRequestAction, request: Request, business: BusinessOut = Depends(get_owned_business)
):
    return await _trigger_and_record(
        request, business, "hr", "recruitment_request", payload.model_dump()
    )


@router.post("/operations/actions/resource-request")
async def operations_resource_request(
    payload: ResourceRequestAction, request: Request, business: BusinessOut = Depends(get_owned_business)
):
    return await _trigger_and_record(
        request, business, "operations", "resource_request", payload.model_dump()
    )
