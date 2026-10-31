"""One validated action contract for API, chat, simulation and CEO proposals."""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class Action(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class BudgetRequestAction(Action):
    amount: float = Field(gt=0)
    department: str = Field(default="General", min_length=1, max_length=100)


class CampaignLaunchAction(Action):
    campaign_name: str = Field(min_length=1, max_length=200)
    requested_budget: float = Field(default=5000, gt=0)


class InstagramPostAction(Action):
    content: str = Field(min_length=1, max_length=10000)


class ReelRequestAction(Action):
    campaign_name: str = Field(min_length=1, max_length=200)
    brief: str = Field(default="", max_length=10000)


class RecruitmentRequestAction(Action):
    role: str = Field(min_length=1, max_length=200)
    headcount: int = Field(default=1, gt=0, le=1000)
    monthly_salary: float = Field(default=3000, ge=0)


class ResourceRequestAction(Action):
    resource_type: str = Field(min_length=1, max_length=200)
    quantity: int = Field(default=1, gt=0)
    unit_cost: float = Field(default=100, ge=0)


ACTION_CONTRACTS = {
    "budget_request": ("finance", BudgetRequestAction),
    "campaign_launch": ("marketing", CampaignLaunchAction),
    "instagram_post": ("marketing", InstagramPostAction),
    "reel_request": ("marketing", ReelRequestAction),
    "recruitment_request": ("hr", RecruitmentRequestAction),
    "resource_request": ("operations", ResourceRequestAction),
}


def validate_action(
    agent: str, action_type: str, payload: dict[str, Any]
) -> dict[str, Any]:
    contract = ACTION_CONTRACTS.get(action_type)
    if contract is None or contract[0] != agent:
        raise ValueError("Unsupported action for this department")
    return contract[1].model_validate(payload).model_dump()
