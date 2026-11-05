"""Contract examples must reject ambiguous or unsafe future work records."""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.models.work_contracts import TaskEnvelopeV1, ApprovalRecordV1, DomainEventV1

NOW = datetime(2026, 11, 5, tzinfo=timezone.utc)


def task(**changes):
    return TaskEnvelopeV1.model_validate(
        {
            "task_id": "task-1",
            "business_id": "business-1",
            "revision": 1,
            "agent": "finance",
            "action_type": "budget_request",
            "payload": {"amount": 25},
            "origin": {"kind": "manual", "actor_id": "owner-1", "actor_kind": "user"},
            "objective": "Allocate budget",
            "success_criteria": "Allocation recorded",
            "created_at": NOW,
            "due_at": NOW + timedelta(days=1),
            **changes,
        }
    )


def test_task_roundtrip_preserves_source_and_normalizes_defaults():
    work = task()
    assert work.payload["department"] == "General"
    assert TaskEnvelopeV1.model_validate_json(work.model_dump_json()) == work
    assert work.mode == "simulation"


@pytest.mark.parametrize(
    "changes",
    [
        {"due_at": datetime(2026, 11, 6)},
        {"due_at": NOW - timedelta(days=1)},
        {"dependencies": ["task-1"]},
        {"dependencies": ["other", "other"]},
        {"agent": "hr"},
        {"payload": {"amount": -1}},
        {"payload": {"amount": float("nan")}},
        {"owner_approved": True},
        {"revision": 0},
    ],
)
def test_invalid_or_forged_task_records_rejected(changes):
    with pytest.raises(ValidationError):
        task(**changes)


def test_deadline_offsets_are_serialized_as_utc():
    work = task(due_at=datetime(2026, 11, 6, 5, tzinfo=timezone(timedelta(hours=5))))
    assert work.due_at == NOW + timedelta(days=1)
    assert work.due_at.utcoffset() == timedelta(0)


def test_fingerprint_is_stable_and_covers_material_edits():
    original = task()
    same = task(payload={"department": "General", "amount": 25})
    assert original.fingerprint() == same.fingerprint()
    for changes in (
        {"payload": {"amount": 26}},
        {"revision": 2},
        {"business_id": "other"},
        {"mode": "live"},
        {"due_at": NOW + timedelta(days=2)},
        {"dependencies": ["prerequisite"]},
        {"policy_version": 2},
    ):
        assert task(**changes).fingerprint() != original.fingerprint()


def approval(**changes):
    work = task()
    return ApprovalRecordV1.model_validate(
        {
            "approval_id": "approval-1",
            "business_id": work.business_id,
            "task_id": work.task_id,
            "revision": 1,
            "task_digest": work.fingerprint(),
            "decision": "approve",
            "stage": "owner",
            "decided_by": "owner-1",
            "reason": "Within owner budget",
            "decided_at": NOW,
            "expires_at": NOW + timedelta(hours=1),
            **changes,
        }
    )


def test_approval_requires_version_digest_actor_and_finite_lifetime():
    assert approval().revision == 1
    for changes in (
        {"revision": 0},
        {"task_digest": "not-a-digest"},
        {"decided_by": ""},
        {"expires_at": NOW},
        {"expires_at": datetime(2026, 11, 6)},
        {"reason": " "},
        {"stage": "agent-self-approval"},
    ):
        with pytest.raises(ValidationError):
            approval(**changes)


def test_event_has_tenant_sequence_and_evidence_reference_only():
    event = DomainEventV1(
        event_id="event-1",
        business_id="business-1",
        task_id="task-1",
        revision=1,
        sequence=1,
        event_type="task.proposed",
        occurred_at=NOW,
        actor_id="owner-1",
        correlation_id="objective-1",
    )
    assert DomainEventV1.model_validate_json(event.model_dump_json()) == event
    for changes in (
        {"sequence": 0},
        {"business_id": ""},
        {"event_type": "run_arbitrary_tool"},
        {"payload": {"access_token": "must-not-be-an-event-field"}},
    ):
        with pytest.raises(ValidationError):
            DomainEventV1.model_validate({**event.model_dump(), **changes})
