"""API-facing business request/response schemas"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class BusinessCreate(BaseModel):
    company_name: str = Field(min_length=1)
    industry: str = Field(min_length=1)
    starting_budget: float = Field(default=100000.0, ge=0, allow_inf_nan=False)
    starting_customer_base: int = Field(default=1000, ge=0)
    starting_headcount: int = Field(default=50, ge=0)
    starting_resources: int = Field(default=10000, ge=0)
    enabled_agents: Optional[List[str]] = None


class BusinessOut(BaseModel):
    id: str
    owner_user_id: str
    company_name: str
    industry: str
    starting_budget: float
    starting_customer_base: int
    starting_headcount: int
    starting_resources: int
    enabled_agents: List[str] = []
    created_at: datetime
