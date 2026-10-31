"""Persistent CEO plans and typed departmental assignments."""

from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator
from .action_schemas import validate_action


class GoalIn(BaseModel):
    goal: str = Field(min_length=5, max_length=2000)


class DepartmentAssignment(BaseModel):
    department: Literal["finance", "marketing", "hr", "operations"]
    objective: str = Field(min_length=1, max_length=1000)
    action_type: Literal[
        "budget_request", "campaign_launch", "recruitment_request", "resource_request"
    ]
    payload: dict[str, Any]
    success_criteria: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_contract(self):
        self.payload = validate_action(self.department, self.action_type, self.payload)
        return self


class CEOPlan(BaseModel):
    strategy: str = Field(min_length=1, max_length=4000)
    assignments: list[DepartmentAssignment] = Field(min_length=1, max_length=12)


class CEOReview(BaseModel):
    assessment: str
    next_action: Literal["continue", "revise_plan", "owner_attention"]
    recommendation: str


class TaskAuthorization(BaseModel):
    decision: Literal["approve", "reject", "request_changes", "escalate"]
    reason: str = Field(min_length=1, max_length=2000)
