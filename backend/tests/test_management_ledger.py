"""Shared-ledger financial invariants and mandatory CEO gate."""

import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from mongomock_motor import AsyncMongoMockClient
from app.services import ledger
from tests.test_execution_supervision import account, business, client, pending


@pytest.fixture(params=["mongo", "fallback"])
def money(request):
    from app.database.mongodb import InMemoryDatabase

    db = AsyncMongoMockClient().test if request.param == "mongo" else InMemoryDatabase()
    return (
        db,
        SimpleNamespace(id=str(uuid4()), starting_budget=1000),
        SimpleNamespace(agent_manager=SimpleNamespace(agents={})),
    )


def task(kind="campaign_launch", **payload):
    return {
        "task_id": str(uuid4()),
        "agent": "marketing",
        "action_type": kind,
        "payload": payload or {"requested_budget": 700},
    }


@pytest.mark.asyncio
async def test_concurrent_reservations_cannot_overdraw(money):
    outcomes = await asyncio.gather(
        *(ledger.reserve(*money, task()) for _ in range(2)), return_exceptions=True
    )
    assert (
        sum(isinstance(x, HTTPException) and x.status_code == 409 for x in outcomes)
        == 1
    )
    a = await ledger.account_for(*money)
    assert (a["cash_minor"], a["reserved_minor"], ledger.available(a)) == (
        100000,
        70000,
        30000,
    )


@pytest.mark.asyncio
async def test_allocation_partial_settlement_release_and_idempotency(money):
    allocation = task("budget_request", amount=600, department="Marketing")
    await ledger.reserve(*money, allocation)
    a = await ledger.settle(*money, allocation, 60000, allocation=True)
    assert a["cash_minor"] == 100000 and a["expenses_minor"] == 0
    work = task(requested_budget=700)
    await ledger.reserve(*money, work)
    with pytest.raises(HTTPException):
        await ledger.release_allocation(*money, allocation["task_id"])
    a = await ledger.settle(*money, work, 50000)
    assert (a["cash_minor"], a["reserved_minor"], a["expenses_minor"]) == (
        50000,
        10000,
        50000,
    )
    b = await ledger.settle(*money, work, 50000)
    assert b["version"] == a["version"]
    a = await ledger.release_allocation(*money, allocation["task_id"])
    assert a["reserved_minor"] == 0 and ledger.available(a) == 50000


@pytest.mark.asyncio
async def test_denial_returns_allocation_and_income_is_idempotent(money):
    allocation = task("budget_request", amount=600, department="General")
    await ledger.reserve(*money, allocation)
    await ledger.settle(*money, allocation, 60000, allocation=True)
    work = task(requested_budget=700)
    await ledger.reserve(*money, work)
    a = await ledger.settle(*money, work, 0)
    assert a["reserved_minor"] == 60000 and a["cash_minor"] == 100000
    a = await ledger.credit(*money, 123, "run-1-tick-5")
    b = await ledger.credit(*money, 123, "run-1-tick-5")
    assert a["version"] == b["version"] and b["revenue_minor"] == 123


@pytest.mark.parametrize("value", ["NaN", "Infinity", -1])
def test_invalid_money(value):
    with pytest.raises(HTTPException):
        ledger.minor(value)


def test_money_rounding():
    assert ledger.minor("1.005") == 101


def test_department_filter_and_finances_are_owner_scoped(client):
    owner = account(client)
    bid = business(client, owner)
    pending(client, owner, bid)
    rows = client.get(
        f"/api/businesses/{bid}/tasks?agent=finance", headers=owner
    ).json()
    assert len(rows) == 1 and rows[0]["ceo_authorized"]
    assert rows[0]["ceo_review"]["basis"] == "operating_policy"
    assert (
        client.get(f"/api/businesses/{bid}/tasks?agent=hr", headers=owner).json() == []
    )
    other = account(client, "other@example.com")
    for suffix in ("tasks?agent=finance", "finances"):
        assert (
            client.get(f"/api/businesses/{bid}/{suffix}", headers=other).status_code
            == 403
        )


def test_revision_rechecks_ceo_and_hr_cost_reaches_ledger(client):
    owner = account(client)
    bid = business(client, owner)
    tid = pending(
        client,
        owner,
        bid,
        "hr",
        "recruitment-request",
        {"role": "Engineer", "headcount": 1, "monthly_salary": 2000},
    )
    revised = client.post(
        f"/api/tasks/{tid}/revise",
        headers=owner,
        json={"payload": {"role": "Engineer", "headcount": 1, "monthly_salary": 2500}},
    )
    assert revised.status_code == 200 and revised.json()["ceo_authorized"]
    executed = client.post(f"/api/tasks/{tid}/approve", headers=owner)
    assert executed.status_code == 200 and executed.json()["status"] == "executed"
    a = client.get(f"/api/businesses/{bid}/finances", headers=owner).json()
    assert (
        a["cash"],
        a["expenses"],
        a["monthly_payroll_commitment"],
        a["reserved"],
    ) == (97500, 2500, 2500, 0)
    assert (
        client.post(
            f"/api/tasks/{tid}/revise",
            headers=owner,
            json={"payload": {"role": "Engineer", "headcount": 1}},
        ).status_code
        == 409
    )


def test_sensitive_action_fails_closed_when_ceo_model_offline(client):
    owner = account(client)
    bid = business(client, owner)
    tid = pending(
        client, owner, bid, "marketing", "instagram-post", {"content": "Test"}
    )
    proposal = client.get(
        f"/api/businesses/{bid}/tasks?agent=marketing", headers=owner
    ).json()[0]
    assert proposal["status"] == "pending_ceo_review" and not proposal["ceo_authorized"]
    assert client.post(f"/api/tasks/{tid}/approve", headers=owner).status_code == 409


def test_unauthorized_execution_and_terminal_reopening_are_blocked(client):
    from app.main import app
    from app.services.tasks import execute_task, review_task
    from app.api.routes.businesses import _to_business_out

    owner = account(client)
    bid = business(client, owner)
    tid = pending(client, owner, bid)

    async def bypass():
        db = app.state.db
        biz = _to_business_out(await db.businesses.find_one({"business_id": bid}))
        await db.tasks.update_one(
            {"task_id": tid}, {"$set": {"ceo_authorized": False, "status": "approved"}}
        )
        proposal = await db.tasks.find_one({"task_id": tid})
        with pytest.raises(HTTPException):
            await execute_task(db, app.state.agent_registry, biz, proposal)
        proposal["status"] = "executed"
        with pytest.raises(HTTPException):
            await review_task(db, app.state.agent_registry, biz, proposal)

    client.portal.call(bypass)
    assert (
        client.get(f"/api/businesses/{bid}/finances", headers=owner).json()["reserved"]
        == 0
    )


def test_slow_ceo_report_review_does_not_block_department_work(client, monkeypatch):
    from app.main import app

    async def slow_review(self, report):
        await asyncio.sleep(10)
        return {
            "assessment": "Reviewed",
            "next_action": "continue",
            "recommendation": "Proceed",
        }

    monkeypatch.setattr(
        "app.agents.ceo_agent.CEOAgent.review_department_report", slow_review
    )
    owner = account(client)
    bid = business(client, owner)
    first, second = pending(client, owner, bid), pending(client, owner, bid)
    assert (
        client.post(f"/api/tasks/{first}/approve", headers=owner).json()["status"]
        == "executed"
    )
    assert (
        client.post(f"/api/tasks/{second}/approve", headers=owner).json()["status"]
        == "executed"
    )
    reports = client.get(f"/api/businesses/{bid}/ceo/reports", headers=owner).json()
    assert len(reports) == 2 and all(
        r["review_status"] in {"pending", "reviewing"} for r in reports
    )

    async def cancel_jobs():
        jobs = list(app.state.agent_registry._runtimes[bid].review_jobs)
        for job in jobs:
            job.cancel()
        await asyncio.gather(*jobs, return_exceptions=True)

    client.portal.call(cancel_jobs)


def test_chat_and_planning_use_ledger_not_temporary_execution_balance(
    client, monkeypatch
):
    import json
    from app.main import app
    from app.agents.schemas import ChatReply
    from app.models.supervision_schemas import CEOPlan
    from tests.test_chat import FakeChatLLM

    owner = account(client)
    bid = business(client, owner)
    tid = pending(client, owner, bid)
    assert client.post(f"/api/tasks/{tid}/approve", headers=owner).status_code == 200
    finance = app.state.agent_registry._runtimes[bid].agent_manager.agents["finance"]
    finance.budget_pool = (
        200000  # Private spendable balance during an in-flight execution.
    )
    fake = FakeChatLLM(
        [ChatReply(reply="Balance recorded"), ChatReply(reply="Balance recorded")]
    )
    monkeypatch.setattr("app.services.chat.get_groq_llm", lambda *a, **kw: fake)
    for agent in ("finance", "ceo"):
        response = client.post(
            f"/api/businesses/{bid}/agents/{agent}/chat",
            headers=owner,
            json={"content": "Current budget?"},
        )
        assert response.status_code == 200
        line = next(
            line
            for line in fake.last_prompt.splitlines()
            if line.startswith("Your current status: ")
        )
        status = json.loads(line.removeprefix("Your current status: "))
        assert (status["departments"]["finance"] if agent == "ceo" else status)[
            "budget_pool"
        ] == 99900

    async def plan(self, goal, context):
        assert context["departments"]["finance"]["budget_pool"] == 99900
        assert context["finances"]["reserved"] == 100
        return CEOPlan(
            strategy="Preserve cash",
            assignments=[
                {
                    "department": "hr",
                    "action_type": "recruitment_request",
                    "payload": {"role": "Engineer", "headcount": 1},
                    "objective": "Hire one engineer",
                    "success_criteria": "One additional engineer",
                }
            ],
        )

    monkeypatch.setattr("app.agents.ceo_agent.CEOAgent.create_plan", plan)
    assert (
        client.post(
            f"/api/businesses/{bid}/ceo/plans",
            headers=owner,
            json={"goal": "Grow with safe cash reserves"},
        ).status_code
        == 200
    )
    assert finance.budget_pool == 200000
