"""Mongo document shapes.

These are not an ODM — plain dicts are written to Mongo directly; these models
exist to document and validate the shape before insertion.
"""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class UserDocument(BaseModel):
    email: str
    hashed_password: str
    created_at: datetime


class BusinessDocument(BaseModel):
    business_id: str
    owner_user_id: str
    company_name: str
    industry: str
    starting_budget: float
    starting_customer_base: int
    starting_headcount: int
    starting_resources: int
    created_at: datetime


class DecisionLogDocument(BaseModel):
    business_id: str
    simulation_run_id: Optional[str] = None
    tick: Optional[int] = None
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str = "simulation"


class AgentSnapshotDocument(BaseModel):
    business_id: str
    simulation_run_id: Optional[str] = None
    agent_id: str
    state: Dict[str, Any]
    timestamp: datetime


class SimulationRunDocument(BaseModel):
    business_id: str
    run_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: str  # "running" | "stopped" | "completed"
    tick_count: int = 0
    config: Dict[str, Any] = Field(default_factory=dict)


class RunSummaryDocument(BaseModel):
    business_id: str
    run_id: str
    headline: str
    key_decisions: list
    risks: list
    recommendation: str
    created_at: datetime


class AgentPolicyDocument(BaseModel):
    business_id: str
    agent_key: str
    enabled: bool = False
    auto_approve_max: Optional[float] = None
    auto_deny_min: Optional[float] = None
    updated_at: datetime
