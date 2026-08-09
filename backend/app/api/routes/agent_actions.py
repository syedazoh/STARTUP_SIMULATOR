"""Manual per-agent action routes (business-scoped).

Each endpoint fires the same event contract each agent already handles when
reacting to a simulation tick — no new event types, just a user-initiated
entry point instead of the synthetic event generator.
"""
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from ..deps import get_owned_business
from ...models.business_schemas import BusinessOut
from ...services.persistence import record_decision, snapshot_agents

router = APIRouter(prefix="/api/businesses/{business_id}/agents", tags=["agent-actions"])


class BudgetRequestAction(BaseModel):
    amount: float
    department: str = "General"


class CampaignLaunchAction(BaseModel):
    campaign_name: str
    requested_budget: float = 5000


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


@router.post("/finance/actions/budget-request")
async def finance_budget_request(
    payload: BudgetRequestAction, request: Request, business: BusinessOut = Depends(get_owned_business)
):
    return await _trigger_and_record(
        request, business, "finance", "budget_request", payload.model_dump()
    )


@router.post("/marketing/actions/campaign-launch")
async def marketing_campaign_launch(
    payload: CampaignLaunchAction, request: Request, business: BusinessOut = Depends(get_owned_business)
):
    return await _trigger_and_record(
        request, business, "marketing", "campaign_launch", payload.model_dump()
    )


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
