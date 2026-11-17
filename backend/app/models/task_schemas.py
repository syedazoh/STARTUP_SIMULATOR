"""API-facing task (approval pipeline) schemas.

A task is the one shared unit every agent uses for a consequential action:
create it, decide (auto or by the owner), then execute. Keeping this generic
across agents is what lets Marketing/HR/Operations reuse the same pipeline
later instead of each growing its own approve/deny plumbing.
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

# "draft"/"awaiting_asset" are reachable once media-asset-requiring actions
# exist (Phase 4); nothing sets them yet, but the field stays a free string
# rather than a strict enum so that phase doesn't need a schema migration.
TaskStatus = str


class TaskOut(BaseModel):
    due_at: Optional[str] = None
    deadline_version: int = 0
    id: str
    mode: Optional[str] = None
    revision: Optional[int] = None
    previous_payload: Optional[Dict[str, Any]] = None
    revision_error: Optional[str] = None
    approval_fingerprint: Optional[str] = None
    proposal_digest: Optional[str] = None
    approval_expires_at: Optional[str] = None
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
    defer_execution: bool = False
    owner_feedback: Optional[str] = Field(default=None, max_length=2000)
    expected_fingerprint: Optional[str] = Field(default=None, pattern=r"^[a-f0-9]{64}$")


def to_task_out(doc: Dict[str, Any]) -> TaskOut:
    return TaskOut(
        id=doc["task_id"],
        due_at=doc.get("due_at"),
        deadline_version=doc.get("deadline_version", 0),
        approval_fingerprint=approval_fingerprint(doc),
        mode=doc.get("mode"),
        previous_payload=doc.get("previous_payload"),
        revision_error=doc.get("revision_error"),
        revision=doc.get("revision"),
        proposal_digest=doc.get("proposal_digest"),
        approval_expires_at=doc.get("approval_expires_at"),
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


# Exact proposal fields guarded for opt-in command-center decisions. This is
# additive preview binding, not the planned immutable task-version migration.
APPROVAL_FIELDS = (
    "due_at",
    "deadline_version",
    "business_id",
    "task_id",
    "agent",
    "action_type",
    "payload",
    "status",
    "objective",
    "success_criteria",
    "source",
    "plan_id",
    "requires_asset",
    "asset_id",
    "mode",
    "revision",
    "proposal_digest",
    "approval_expires_at",
)


def approval_fingerprint(doc: Dict[str, Any]) -> str:
    proposal = {field: doc.get(field) for field in APPROVAL_FIELDS}
    return hashlib.sha256(
        json.dumps(
            proposal,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
            allow_nan=False,
        ).encode()
    ).hexdigest()
