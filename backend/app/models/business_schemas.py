"""API-facing business request/response schemas"""
from datetime import datetime
from typing import List, Optional, Literal, Annotated

from pydantic import BaseModel, Field, model_validator, StringConstraints


TeamText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]

class WorkforcePosition(BaseModel):
    department: TeamText
    role: TeamText
    count: int = Field(strict=True, gt=0, le=1000000)
    employment_type: Literal["full_time", "part_time", "contract", "intern", "unspecified"] = "unspecified"

class Workforce(BaseModel):
    total_headcount: int = Field(strict=True, ge=0, le=1000000)
    positions: List[WorkforcePosition] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def valid_breakdown(self):
        if sum(row.count for row in self.positions) > self.total_headcount:
            raise ValueError("Department counts exceed total headcount; remaining people are not assigned yet.")
        keys = [(row.department.casefold(), row.role.casefold(), row.employment_type) for row in self.positions]
        if len(keys) != len(set(keys)):
            raise ValueError("Combine duplicate department, role and employment groups.")
        return self


class BusinessCreate(BaseModel):
    company_name: str = Field(min_length=1)
    industry: str = Field(min_length=1)
    starting_budget: float = Field(default=100000.0, ge=0, allow_inf_nan=False)
    starting_customer_base: int = Field(default=1000, ge=0)
    starting_headcount: int = Field(default=50, ge=0)
    starting_resources: int = Field(default=10000, ge=0)
    enabled_agents: Optional[List[str]] = None
    workforce: Optional[Workforce] = None

    @model_validator(mode="after")
    def matching_team(self):
        if self.workforce and self.workforce.total_headcount != self.starting_headcount:
            raise ValueError("Team total must match starting headcount.")
        return self


class BusinessOut(BaseModel):
    id: str
    owner_user_id: str
    company_name: str
    industry: str
    starting_budget: float
    starting_customer_base: int
    starting_headcount: int
    starting_resources: int
    workforce: Optional[Workforce] = None
    enabled_agents: List[str] = []
    created_at: datetime
