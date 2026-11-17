import asyncio
from datetime import datetime, timedelta, timezone
import pytest
from tests.test_account_isolation import accounts  # noqa: F401
from app.config import settings
from app.services import jobs, deadlines


@pytest.fixture(autouse=True)
def configured_worker_without_loop(monkeypatch):
    monkeypatch.setattr(settings, "background_jobs_enabled", True)
    monkeypatch.setattr(settings, "rag_dense_enabled", False)
    monkeypatch.setattr(settings, "rag_reranker_enabled", False)

    async def idle(app):
        await asyncio.Event().wait()

    monkeypatch.setattr(jobs, "worker_loop", idle)


def proposal(c, h, a):
    return c.post(
        f"/api/businesses/{a}/agents/finance/actions/budget-request",
        headers=h["alice"],
        json={"amount": 25},
    ).json()


def test_queue_owner_scoping_and_cancel(accounts):
    c, h, a, b = accounts
    r = c.post(
        f"/api/businesses/{a}/jobs",
        headers=h["alice"],
        json={"kind": "daily_brief", "idempotency_key": "one"},
    )
    assert r.status_code == 202
    assert c.get(f"/api/businesses/{a}/automation", headers=h["bob"]).status_code == 403
    assert (
        c.post(
            f"/api/businesses/{b}/jobs/{r.json()['job_id']}/cancel", headers=h["bob"]
        ).status_code
        == 404
    )
    assert (
        c.post(
            f"/api/businesses/{a}/jobs/{r.json()['job_id']}/cancel", headers=h["alice"]
        ).json()["status"]
        == "cancelled"
    )


def test_deferred_approval_outbox_recovers_and_executes_once(accounts):
    c, h, a, _ = accounts
    t = proposal(c, h, a)
    r = c.post(
        f"/api/tasks/{t['id']}/approve",
        headers=h["alice"],
        json={
            "defer_execution": True,
            "expected_fingerprint": t["approval_fingerprint"],
        },
    )
    assert (
        r.status_code == 200
        and r.json()["status"] == "approved"
        and r.json()["result"] is None
    )
    db = c.app.state.db
    asyncio.run(db["background_jobs"].delete_many({}))
    asyncio.run(jobs.reconcile(db))
    assert (
        asyncio.run(jobs.run_once(db, c.app.state.agent_registry))["status"]
        == "succeeded"
    )
    assert (
        c.get(f"/api/tasks/{t['id']}", headers=h["alice"]).json()["status"]
        == "executed"
    )
    assert asyncio.run(jobs.run_once(db, c.app.state.agent_registry)) is None


def test_deadline_versioned_deduplicated_notifications(accounts):
    c, h, a, _ = accounts
    t = proposal(c, h, a)
    now = datetime.now(timezone.utc)
    body = {
        "due_at": (now + timedelta(hours=1)).isoformat(),
        "expected_version": 0,
        "reason": "Launch commitment",
        "reminder_minutes": 60,
        "escalation_minutes": 10,
    }
    url = f"/api/tasks/{t['id']}/deadline"
    assert c.put(url, headers=h["alice"], json=body).json()["deadline_version"] == 1
    assert c.put(url, headers=h["alice"], json=body).status_code == 409
    assert c.put(url, headers=h["bob"], json=body).status_code == 403
    for _ in range(2):
        asyncio.run(deadlines.scan_deadlines(c.app.state.db, now.timestamp() + 5000))
    assert len(asyncio.run(deadlines.notifications(c.app.state.db, a))) == 3
    body.update(expected_version=1, due_at=(now + timedelta(hours=4)).isoformat())
    assert c.put(url, headers=h["alice"], json=body).status_code == 200
    assert asyncio.run(deadlines.notifications(c.app.state.db, a)) == []


def test_invalid_date_and_synchronous_cutoff(accounts):
    c, h, a, _ = accounts
    t = proposal(c, h, a)
    url = f"/api/tasks/{t['id']}/deadline"
    for date in ["2020-01-01T00:00:00", "2020-01-01T00:00:00Z"]:
        assert (
            c.put(
                url,
                headers=h["alice"],
                json={"due_at": date, "expected_version": 0, "reason": "test"},
            ).status_code
            == 422
        )
    asyncio.run(
        c.app.state.db["tasks"].update_one(
            {"task_id": t["id"]},
            {
                "$set": {
                    "due_ts": 1,
                    "due_at": "1970-01-01T00:00:01Z",
                    "deadline_version": 1,
                }
            },
        )
    )
    fresh = c.get(f"/api/tasks/{t['id']}", headers=h["alice"]).json()
    assert (
        c.post(
            f"/api/tasks/{t['id']}/approve",
            headers=h["alice"],
            json={"expected_fingerprint": fresh["approval_fingerprint"]},
        ).status_code
        == 409
    )
    assert (
        c.get(f"/api/tasks/{t['id']}", headers=h["alice"]).json()["status"] == "expired"
    )
