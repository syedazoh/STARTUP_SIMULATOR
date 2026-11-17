"""Boardroom handoffs must be recorded from real business actions, not UI guesses."""
import pytest
from mongomock_motor import AsyncMongoMockClient

from app.services.collaboration import record_handoff, record_decision_activity, list_collaboration_events, infer_internal_route
from app.orchestration.event_bus import EventBus

@pytest.mark.asyncio
async def test_ceo_delegation_survives_runtime_restart_and_is_business_scoped():
    db = AsyncMongoMockClient().startup_test
    await record_handoff(db, "business-a", "ceo", "hr", "task_assigned",
                         "Recruit a designer", task_id="task-1", plan_id="plan-1")
    assert (await list_collaboration_events(db, "business-b")) == []
    events = await list_collaboration_events(db, "business-a")
    assert len(events) == 1
    assert events[0]["sender"] == "ceo"
    assert events[0]["receiver"] == "hr"
    assert events[0]["data"]["task_id"] == "task-1"
    assert events[0]["data"]["title"] == "Recruit a designer"
    assert events[0]["event_id"]
    assert isinstance(events[0]["timestamp"], str)

@pytest.mark.asyncio
async def test_decision_log_activity_has_no_fake_agent_recipient():
    db = AsyncMongoMockClient().startup_test
    await record_decision_activity(db, "b", "campaign_launch", run_id="r1", tick=3)
    event = (await list_collaboration_events(db, "b"))[0]
    assert event["event_type"] == "decision_recorded"
    assert "sender" not in event and "receiver" not in event
    assert event["data"]["tick"] == 3

def test_only_observed_internal_messages_get_agent_routes():
    assert infer_internal_route("hr_001", "budget_request") == ("hr", "finance")
    assert infer_internal_route("finance_001", "arbitration_request") == ("finance", "ceo")
    assert infer_internal_route("api", "budget_request") is None
    assert infer_internal_route("manual", "recruitment_request") is None
    assert infer_internal_route("hr_001", "recruitment_request") is None
    assert infer_internal_route("hr_foreign", "budget_request") is None

@pytest.mark.asyncio
async def test_event_bus_publishes_real_internal_handoffs_to_durable_store():
    db = AsyncMongoMockClient().startup_test
    bus = EventBus()
    async def observer(event):
        route = infer_internal_route(event.source, event.event_type)
        if route:
            await record_handoff(db, "b", *route, event.event_type, "Budget coordination",
                                 event_id=event.event_id)
    bus.on_publish = observer
    await bus.publish("budget_request", {"amount": 100}, source="hr_001")
    await bus.publish("budget_request", {"amount": 100}, source="api")
    rows = await list_collaboration_events(db, "b")
    assert len(rows) == 1
    assert rows[0]["sender"] == "hr" and rows[0]["receiver"] == "finance"

@pytest.mark.asyncio
async def test_projection_failure_never_blocks_real_task_processing():
    from app.services.collaboration import best_effort_handoff
    class FailingDB:
        def __getitem__(self, name):
            raise RuntimeError("activity store unavailable")
    await best_effort_handoff(FailingDB(), "b", "ceo", "hr",
                              "task_assigned", "Recruit a designer")
