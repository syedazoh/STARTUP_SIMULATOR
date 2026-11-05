"""Reference v1 contracts for T02; runtime adoption belongs to T07–T14.

These data validators do not authenticate actors, allocate event sequences,
apply state transitions, persist approvals or authorize tool execution.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    field_validator,
    model_validator,
)

from .action_schemas import validate_action

Identifier = Annotated[
    str, Field(min_length=1, max_length=200, pattern=r"^\S(?:.*\S)?$")
]
Department = Literal["finance", "marketing", "hr", "operations", "ceo"]
TaskState = Literal[
    "draft",
    "pending_ceo_review",
    "ceo_reviewing",
    "pending_approval",
    "awaiting_asset",
    "needs_changes",
    "needs_revision",
    "approved",
    "auto_approved",
    "queued",
    "executing",
    "awaiting_external",
    "executed",
    "verified_complete",
    "failed",
    "denied",
    "rejected",
    "cancelled",
    "expired",
    "reconciliation_required",
]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    @field_validator("*")
    @classmethod
    def utc_dates(cls, value):
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc)
        return value


class TaskOriginV1(Contract):
    kind: Literal[
        "manual",
        "chat",
        "ceo_plan",
        "simulation",
        "schedule",
        "webhook",
        "owner_revision",
    ]
    actor_kind: Literal["user", "agent", "system"]
    actor_id: Identifier
    source_event_id: Identifier | None = None
    parent_task_id: Identifier | None = None
    plan_id: Identifier | None = None
    run_id: Identifier | None = None


class TaskEnvelopeV1(Contract):
    schema_version: Literal[1] = 1
    task_id: Identifier
    business_id: Identifier
    revision: int = Field(ge=1, strict=True)
    agent: Department
    action_type: Identifier
    payload: dict[str, JsonValue]
    origin: TaskOriginV1
    objective: Annotated[str, Field(min_length=1, max_length=1000, pattern=r"\S")]
    success_criteria: Annotated[
        str, Field(min_length=1, max_length=2000, pattern=r"\S")
    ]
    mode: Literal["simulation", "sandbox", "live"] = "simulation"
    status: TaskState = "draft"
    priority: Literal["low", "normal", "high", "urgent"] = "normal"
    policy_version: int = Field(default=1, ge=1, strict=True)
    created_at: AwareDatetime
    due_at: AwareDatetime | None = None
    dependencies: list[Identifier] = Field(default_factory=list, max_length=100)
    idempotency_key: Identifier | None = None

    @model_validator(mode="after")
    def validate_proposal(self):
        self.payload = validate_action(self.agent, self.action_type, self.payload)
        if self.due_at is not None and self.due_at <= self.created_at:
            raise ValueError("Deadline must follow creation")
        if self.task_id in self.dependencies or len(set(self.dependencies)) != len(
            self.dependencies
        ):
            raise ValueError("Dependencies must be unique and cannot include self")
        return self

    def fingerprint(self) -> str:
        """Digest of a normalized proposal snapshot, not an authorization token."""
        # Revalidate because nested payload/list values remain mutable in Python.
        normalized = (
            type(self).model_validate(self.model_dump()).model_dump(mode="json")
        )
        canonical = json.dumps(
            normalized,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ApprovalRecordV1(Contract):
    schema_version: Literal[1] = 1
    approval_id: Identifier
    business_id: Identifier
    task_id: Identifier
    revision: int = Field(ge=1, strict=True)
    task_digest: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    stage: Literal["ceo", "owner", "policy"]
    decision: Literal["approve", "reject", "request_changes", "escalate"]
    decided_by: Identifier
    reason: Annotated[str, Field(min_length=1, max_length=2000, pattern=r"\S")]
    policy_version: int = Field(default=1, ge=1, strict=True)
    decided_at: AwareDatetime
    expires_at: AwareDatetime

    @model_validator(mode="after")
    def validate_lifetime(self):
        if self.expires_at <= self.decided_at:
            raise ValueError("Approval expiry must follow decision time")
        return self


class DomainEventV1(Contract):
    schema_version: Literal[1] = 1
    event_id: Identifier
    business_id: Identifier
    task_id: Identifier
    revision: int = Field(ge=1, strict=True)
    sequence: int = Field(ge=1, strict=True)
    event_type: Literal[
        "task.proposed",
        "task.revised",
        "approval.requested",
        "approval.decided",
        "task.queued",
        "task.started",
        "task.blocked",
        "task.executed",
        "task.verified",
        "task.failed",
        "task.overdue",
        "task.cancelled",
        "task.reconciliation_required",
    ]
    actor_id: Identifier
    correlation_id: Identifier
    occurred_at: AwareDatetime
    causation_id: Identifier | None = None
    evidence_ref: Identifier | None = None
