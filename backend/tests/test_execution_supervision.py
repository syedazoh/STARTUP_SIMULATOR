"""Offline regressions for sessions, approval gates and CEO supervision."""

import asyncio
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

from app.main import app
from app.models.supervision_schemas import CEOPlan
from app.services.sessions import COOKIE_NAME
from app.services.tasks import execute_task

SESSION_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "http://localhost:5173",
}


class OfflineLLM:
    def with_structured_output(self, schema):
        return self

    async def ainvoke(self, prompt):
        raise RuntimeError("No external model calls in regression tests")


class Memory:
    def query_similar(self, *args, **kwargs):
        return []

    def add_decision(self, **kwargs):
        pass


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        "app.database.mongodb.AsyncIOMotorClient",
        lambda *a, **kw: AsyncMongoMockClient(),
    )
    monkeypatch.setattr("app.core.llm._cached_groq_llm", lambda *a: OfflineLLM())
    for module in (
        "finance_agent",
        "marketing_agent",
        "hr_agent",
        "operations_agent",
        "ceo_agent",
    ):
        monkeypatch.setattr(
            f"app.agents.{module}.get_decision_memory_store", lambda: Memory()
        )
    with TestClient(app) as test_client:
        yield test_client


def account(client, email="regression@example.com"):
    assert (
        client.post(
            "/api/auth/register", json={"email": email, "password": "supersecret123"}
        ).status_code
        == 201
    )
    response = client.post(
        "/api/auth/login", json={"email": email, "password": "supersecret123"}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def business(client, headers, **kwargs):
    response = client.post(
        "/api/businesses",
        headers=headers,
        json={"company_name": "Test", "industry": "Software", **kwargs},
    )
    assert response.status_code == 201
    return response.json()["id"]


def pending(
    client, headers, bid, agent="finance", action="budget-request", payload=None
):
    response = client.post(
        f"/api/businesses/{bid}/agents/{agent}/actions/{action}",
        headers=headers,
        json=payload or {"amount": 100, "department": "Operations"},
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_refresh_rotation_and_reuse_revoke_access(client):
    headers = account(client)
    old = client.cookies.get(COOKIE_NAME)
    response = client.post("/api/auth/refresh", headers=SESSION_HEADERS)
    assert response.status_code == 200
    assert client.cookies.get(COOKIE_NAME) != old
    access = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert client.get("/api/auth/me", headers=access).status_code == 200
    response = client.post(
        "/api/auth/refresh",
        headers={**SESSION_HEADERS, "Cookie": f"{COOKIE_NAME}={old}"},
    )
    assert response.status_code == 401
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    assert client.get("/api/auth/me", headers=access).status_code == 401


def test_logout_revokes_a_copied_access_token(client):
    headers = account(client)
    assert (
        client.post(
            "/api/auth/logout", headers={**headers, **SESSION_HEADERS}
        ).status_code
        == 204
    )
    assert client.cookies.get(COOKIE_NAME) is None
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    assert client.post("/api/auth/refresh", headers=SESSION_HEADERS).status_code == 401


def test_refresh_requires_custom_header_and_allowed_origin(client):
    account(client)
    assert client.post("/api/auth/refresh").status_code == 403
    assert (
        client.post(
            "/api/auth/refresh",
            headers={**SESSION_HEADERS, "Origin": "https://evil.invalid"},
        ).status_code
        == 403
    )
    assert client.post("/api/auth/refresh", headers=SESSION_HEADERS).status_code == 200


def test_refresh_tokens_are_hashed_and_access_is_short_lived(client):
    from app.core.security import decode_access_claims

    headers = account(client)
    raw = client.cookies.get(COOKIE_NAME)
    docs = client.portal.call(
        lambda: app.state.db["refresh_tokens"].find({}).to_list(length=10)
    )
    assert raw not in str(docs)
    claims = decode_access_claims(headers["Authorization"][7:])
    assert 0 < claims["exp"] - datetime.now(timezone.utc).timestamp() <= 15 * 60
    assert claims["sid"]


def test_secure_cookie_in_production(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "debug", False)
    client.post(
        "/api/auth/register",
        json={"email": "secure@example.com", "password": "supersecret123"},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "secure@example.com", "password": "supersecret123"},
    )
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "Secure" in cookie and "SameSite=strict" in cookie


def test_legacy_stateless_token_requires_new_login(client):
    from app.core.security import create_access_token

    account(client)
    token = create_access_token("any-user")
    assert (
        client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 401
    )


def test_fallback_database_can_login_and_clear_failed_attempts(client, monkeypatch):
    from app.database.mongodb import InMemoryDatabase

    app.state.db = InMemoryDatabase()
    headers = account(client)
    assert client.get("/api/auth/me", headers=headers).status_code == 200
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "regression@example.com", "password": "bad"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "regression@example.com", "password": "supersecret123"},
        ).status_code
        == 200
    )


def test_event_api_cannot_bypass_owner_approval(client):
    headers = account(client)
    bid = business(client, headers)
    response = client.post(
        f"/api/businesses/{bid}/events",
        headers=headers,
        json={
            "event_type": "recruitment_request",
            "data": {"role": "Engineer", "headcount": 2},
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    status = client.get(f"/api/businesses/{bid}/agents/hr", headers=headers).json()
    assert status["employee_count"] == 50
    tasks = client.get(f"/api/businesses/{bid}/tasks", headers=headers).json()
    assert tasks[0]["status"] == "pending_approval"


def test_simulation_submits_tasks_without_applying_them(client, monkeypatch):
    monkeypatch.setattr(
        "app.simulation.simulation_engine.generate_event",
        lambda **kwargs: (
            "budget_request",
            {"amount": 100, "department": "Operations"},
        ),
    )
    headers = account(client)
    bid = business(client, headers)
    response = client.post(
        f"/api/businesses/{bid}/simulation/start",
        headers=headers,
        json={"ticks": 1, "min_interval": 0.1, "max_interval": 0.1},
    )
    assert response.status_code == 200
    client.portal.call(asyncio.sleep, 0.2)
    tasks = client.get(f"/api/businesses/{bid}/tasks", headers=headers).json()
    assert len(tasks) == 1 and tasks[0]["status"] == "pending_approval"
    assert tasks[0]["source"] == "simulation"
    assert (
        client.get(f"/api/businesses/{bid}/agents/finance", headers=headers).json()[
            "budget_pool"
        ]
        == 100000
    )


@pytest.mark.parametrize("payload", [{"amount": -1}, {"amount": 0}, {"amount": "NaN"}])
def test_invalid_actions_are_rejected_before_queueing(client, payload):
    headers = account(client)
    bid = business(client, headers)
    assert (
        client.post(
            f"/api/businesses/{bid}/agents/finance/actions/budget-request",
            headers=headers,
            json=payload,
        ).status_code
        == 422
    )
    assert client.get(f"/api/businesses/{bid}/tasks", headers=headers).json() == []


def test_failed_external_result_is_not_success(client, monkeypatch):
    async def authorize(self, task, context):
        return {
            "decision": "approve",
            "basis": "test",
            "reason": "Test CEO authorization",
        }

    monkeypatch.setattr("app.agents.ceo_agent.CEOAgent.authorize_task", authorize)

    async def failed(*args):
        return {"status": "failed", "reason": "provider_unavailable"}

    monkeypatch.setitem(
        __import__(
            "app.services.tasks", fromlist=["EXTERNAL_ACTION_HANDLERS"]
        ).EXTERNAL_ACTION_HANDLERS,
        "instagram_post",
        failed,
    )
    headers = account(client)
    bid = business(client, headers)
    tid = pending(
        client, headers, bid, "marketing", "instagram-post", {"content": "Test"}
    )
    response = client.post(f"/api/tasks/{tid}/approve", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "failed"

    async def await_reviews():
        runtime = app.state.agent_registry._runtimes[bid]
        await asyncio.gather(*runtime.review_jobs)

    client.portal.call(await_reviews)
    reports = client.get(f"/api/businesses/{bid}/ceo/reports", headers=headers).json()
    assert reports[0]["status"] == "failed"
    assert reports[0]["ceo_review"]["next_action"] == "owner_attention"


def test_execution_claim_prevents_double_effects(client):
    headers = account(client)
    bid = business(client, headers)
    tid = pending(client, headers, bid)

    async def race():
        from app.api.routes.businesses import _to_business_out

        db = app.state.db
        await db["tasks"].update_one({"task_id": tid}, {"$set": {"status": "approved"}})
        task = (await db["tasks"].find({"task_id": tid}).to_list(length=1))[0]
        biz = _to_business_out(
            (await db["businesses"].find({"business_id": bid}).to_list(length=1))[0]
        )
        return await asyncio.gather(
            execute_task(db, app.state.agent_registry, biz, task),
            execute_task(db, app.state.agent_registry, biz, task),
            return_exceptions=True,
        )

    results = client.portal.call(race)
    assert (
        sum(isinstance(r, HTTPException) and r.status_code == 409 for r in results) == 1
    )
    assert (
        client.get(f"/api/businesses/{bid}/agents/finance", headers=headers).json()[
            "budget_pool"
        ]
        == 99900
    )
    assert (
        len(client.get(f"/api/businesses/{bid}/ceo/reports", headers=headers).json())
        == 1
    )


def test_ceo_delegates_and_receives_department_reports(client, monkeypatch):
    async def plan(self, goal, context):
        assert "departments" in context
        return CEOPlan(
            strategy="Build capacity carefully",
            assignments=[
                {
                    "department": "hr",
                    "objective": "Hire one engineer",
                    "action_type": "recruitment_request",
                    "payload": {"role": "Engineer", "headcount": 1},
                    "success_criteria": "One additional engineer",
                }
            ],
        )

    monkeypatch.setattr("app.agents.ceo_agent.CEOAgent.create_plan", plan)
    headers = account(client)
    bid = business(client, headers)
    base = f"/api/businesses/{bid}/ceo"
    response = client.post(
        f"{base}/plans", headers=headers, json={"goal": "Increase delivery capacity"}
    )
    assert response.status_code == 200
    pid = response.json()["plan_id"]
    assert client.get(f"/api/businesses/{bid}/tasks", headers=headers).json() == []
    assigned = client.post(f"{base}/plans/{pid}/activate", headers=headers)
    assert assigned.status_code == 200
    assert (
        client.post(f"{base}/plans/{pid}/activate", headers=headers).status_code == 409
    )
    tasks = client.get(f"/api/businesses/{bid}/tasks", headers=headers).json()
    assert tasks[0]["plan_id"] == pid and tasks[0]["status"] == "pending_approval"
    personal = client.get(
        f"/api/businesses/{bid}/tasks?agent=hr", headers=headers
    ).json()
    assert personal[0]["objective"] == "Hire one engineer"
    assert personal[0]["success_criteria"] == "One additional engineer"
    assert personal[0]["ceo_review"]["basis"] == "ceo_plan"
    assert (
        client.get(f"/api/businesses/{bid}/tasks?agent=finance", headers=headers).json()
        == []
    )
    assert (
        client.post(f"/api/tasks/{tasks[0]['id']}/approve", headers=headers).json()[
            "status"
        ]
        == "executed"
    )
    report = client.get(f"{base}/reports", headers=headers).json()[0]
    assert report["department"] == "hr" and report["plan_id"] == pid
    assert (
        report["before"]["employee_count"] == 50
        and report["after"]["employee_count"] == 51
    )
    assert report["success_criteria"] == "One additional engineer"
    outsider = account(client, "outsider@example.com")
    assert client.get(f"{base}/reports", headers=outsider).status_code == 403
    assert (
        client.post(f"{base}/plans/{pid}/activate", headers=outsider).status_code == 403
    )


def test_owner_rejection_reports_blocked_work_to_ceo(client):
    headers = account(client)
    bid = business(client, headers)
    tid = pending(client, headers, bid)
    client.post(
        f"/api/tasks/{tid}/reject",
        headers=headers,
        json={"owner_feedback": "Hold spending"},
    )
    assert (
        client.get(f"/api/businesses/{bid}/ceo/reports", headers=headers).json()[0][
            "status"
        ]
        == "rejected"
    )


def test_handler_errors_are_propagated():
    from app.orchestration.event_bus import EventBus

    async def run():
        bus = EventBus()

        async def fail(event):
            raise RuntimeError("handler failed")

        bus.subscribe("test", fail)
        with pytest.raises(RuntimeError, match="handler failed"):
            await bus.publish("test", {})

    asyncio.run(run())


def test_every_department_reports_to_ceo(client):
    headers = account(client)
    bid = business(client, headers)
    actions = [
        ("finance", "budget-request", {"amount": 100}),
        (
            "marketing",
            "campaign-launch",
            {"campaign_name": "Test", "requested_budget": 100},
        ),
        ("hr", "recruitment-request", {"role": "Engineer", "headcount": 1}),
        ("operations", "resource-request", {"resource_type": "Compute", "quantity": 1}),
    ]
    for agent, action, payload in actions:
        tid = pending(client, headers, bid, agent, action, payload)
        assert (
            client.post(f"/api/tasks/{tid}/approve", headers=headers).json()["status"]
            == "executed"
        )
    reports = client.get(f"/api/businesses/{bid}/ceo/reports", headers=headers).json()
    assert {r["department"] for r in reports} == {
        "finance",
        "marketing",
        "hr",
        "operations",
    }
    assert all("ceo_review" in r for r in reports)


def test_expired_session_blocks_both_access_and_refresh(client):
    headers = account(client)
    from app.core.security import decode_access_claims

    sid = decode_access_claims(headers["Authorization"][7:])["sid"]
    client.portal.call(
        lambda: app.state.db["sessions"].update_one(
            {"session_id": sid}, {"$set": {"expires_ts": 0}}
        )
    )
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    assert client.post("/api/auth/refresh", headers=SESSION_HEADERS).status_code == 401


def test_production_refuses_database_fallback(monkeypatch):
    from app.config import settings
    from app.database.mongodb import connect_to_mongo

    def unavailable(*args, **kwargs):
        raise ConnectionError("Database unavailable")

    monkeypatch.setattr(settings, "debug", False)
    monkeypatch.setattr("app.database.mongodb.AsyncIOMotorClient", unavailable)
    with pytest.raises(RuntimeError, match="MongoDB is required"):
        asyncio.run(connect_to_mongo())


def test_plan_marks_completed_after_its_assignment_reports(client, monkeypatch):
    async def plan(self, goal, context):
        return CEOPlan(
            strategy="Manage spending",
            assignments=[
                {
                    "department": "finance",
                    "objective": "Allocate a small budget",
                    "action_type": "budget_request",
                    "payload": {"amount": 100},
                    "success_criteria": "Budget allocated",
                }
            ],
        )

    monkeypatch.setattr("app.agents.ceo_agent.CEOAgent.create_plan", plan)
    headers = account(client)
    bid = business(client, headers)
    base = f"/api/businesses/{bid}/ceo"
    pid = client.post(
        f"{base}/plans", headers=headers, json={"goal": "Manage spending"}
    ).json()["plan_id"]
    client.post(f"{base}/plans/{pid}/activate", headers=headers)
    tid = client.get(f"/api/businesses/{bid}/tasks", headers=headers).json()[0]["id"]
    client.post(f"/api/tasks/{tid}/approve", headers=headers)
    assert (
        client.get(f"{base}/plans", headers=headers).json()[0]["status"] == "completed"
    )
