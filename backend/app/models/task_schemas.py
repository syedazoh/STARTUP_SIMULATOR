"""API-facing task (approval pipeline) schemas.

A task is the one shared unit every agent uses for a consequential action:
create it, decide (auto or by the owner), then execute. Keeping this generic
across agents is what lets Marketing/HR/Operations reuse the same pipeline
later instead of each growing its own approve/deny plumbing.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

# "draft"/"awaiting_asset" are reachable once media-asset-requiring actions
# exist (Phase 4); nothing sets them yet, but the field stays a free string
# rather than a strict enum so that phase doesn't need a schema migration.
TaskStatus = str


class TaskOut(BaseModel):
    id: str
    business_id: str
    agent: str
    source: str = "manual"
    plan_id: Optional[str] = None
    objective: Optional[str] = None
    success_criteria: Optional[str] = None
    ceo_authorized: bool = False
    ceo_review: Optional[Dict[str, Any]] = None
    action_type: str
    payload: Dict[str, Any]
    requires_asset: bool = False
    asset_id: Optional[str] = None
    status: TaskStatus
    owner_feedback: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    decided_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None


class TaskDecisionIn(BaseModel):
    owner_feedback: Optional[str] = Field(default=None, max_length=2000)


def to_task_out(doc: Dict[str, Any]) -> TaskOut:
    return TaskOut(
        id=doc["task_id"],
        business_id=doc["business_id"],
        agent=doc["agent"],
        source=doc.get("source", "manual"),
        plan_id=doc.get("plan_id"),
        objective=doc.get("objective"),
        success_criteria=doc.get("success_criteria"),
        ceo_authorized=doc.get("ceo_authorized", False),
        ceo_review=doc.get("ceo_review"),
        action_type=doc["action_type"],
        payload=doc["payload"],
        requires_asset=doc.get("requires_asset", False),
        asset_id=doc.get("asset_id"),
        status=doc["status"],
        owner_feedback=doc.get("owner_feedback"),
        result=doc.get("result"),
        created_at=doc["created_at"],
        decided_at=doc.get("decided_at"),
        executed_at=doc.get("executed_at"),
    )


class TaskRevisionIn(BaseModel):
    payload: Dict[str, Any]
    objective: Optional[str] = Field(default=None, min_length=1, max_length=1000)
