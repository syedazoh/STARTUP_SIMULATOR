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
    role: str = "owner"  # "owner" | "admin"
    encrypted_data_key: str  # see core/crypto.py — decrypts to this user's Fernet data key
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


class BusinessProfileDocument(BaseModel):
    business_id: str
    brand: Dict[str, Any] = Field(default_factory=dict)
    product: Dict[str, Any] = Field(default_factory=dict)
    marketing: Dict[str, Any] = Field(default_factory=dict)
    finance: Dict[str, Any] = Field(default_factory=dict)
    operations: Dict[str, Any] = Field(default_factory=dict)
    custom_context: list = Field(default_factory=list)
    updated_at: datetime


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


class MediaAssetDocument(BaseModel):
    asset_id: str
    business_id: str
    task_id: str
    uploaded_by: str = "owner"
    file_ref: str
    media_type: str  # "video" | "image"
    agent_review: Dict[str, Any] = Field(default_factory=dict)
    uploaded_at: datetime


class ChatThreadDocument(BaseModel):
    business_id: str
    agent: str
    messages: list = Field(default_factory=list)  # [{role, content, created_at}, ...]
    updated_at: datetime


class CredentialDocument(BaseModel):
    business_id: str
    provider: str
    encrypted_payload: str
    encryption_key_id: str  # user_id whose data key encrypted this payload
    connected_by_user_id: str
    connected_at: datetime
    last_used_at: Optional[datetime] = None
    scopes: list = Field(default_factory=list)


class AgentModeDocument(BaseModel):
    business_id: str
    agent: str
    mode: str = "manual"  # "manual" | "auto"
    auto_thresholds: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime


class TaskDocument(BaseModel):
    task_id: str
    business_id: str
    agent: str
    action_type: str
    payload: Dict[str, Any]
    requires_asset: bool = False
    asset_id: Optional[str] = None
    # "pending_approval" | "auto_approved" | "approved" | "rejected" |
    # "needs_changes" | "executed" | "failed" (see task_schemas.py)
    status: str
    owner_feedback: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    decided_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
