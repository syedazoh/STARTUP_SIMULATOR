"""Owner feedback changes a proposal or leaves an explicit, non-executable blocker."""

import pytest
from tests.test_account_isolation import accounts  # noqa: F401
from app.core import llm


def propose(accounts):
    client, headers, business, _ = accounts
    result = client.post(
        f"/api/businesses/{business}/agents/finance/actions/budget-request",
        headers=headers["alice"],
        json={"amount": 1000},
    )
    assert result.status_code == 200
    return result.json()


def reviser(monkeypatch, payload):
    previous = llm._cached_groq_llm

    class Model:
        def with_structured_output(self, schema):
            if schema.__name__ != "BudgetRequestAction":
                return previous(0).with_structured_output(schema)

            class Structured:
                async def ainvoke(self, prompt):
                    assert "Lower to 400" in prompt
                    return schema.model_validate(payload)

            return Structured()

    monkeypatch.setattr(llm, "_cached_groq_llm", lambda *a: Model())


def test_feedback_changes_payload_without_executing(accounts, monkeypatch):
    client, h, _, _ = accounts
    task = propose(accounts)

    # Only the revision model boundary is replaced; CEO review retains its fixture.
    async def generate(task, feedback):
        return {"amount": 400.0, "department": "General"}

    monkeypatch.setattr("app.services.task_revision.generate_revision", generate)
    response = client.post(
        f"/api/tasks/{task['id']}/request-changes",
        headers=h["alice"],
        json={"owner_feedback": "Lower to 400"},
    )
    assert response.status_code == 200
    revised = response.json()
    assert (
        revised["payload"]["amount"] == 400
        and revised["previous_payload"]["amount"] == 1000
    )
    assert revised["owner_feedback"] == "Lower to 400" and revised["result"] is None
    assert (
        revised["status"] == "pending_approval"
        and revised["source"] == "owner_revision"
    )
    assert revised["approval_fingerprint"] != task["approval_fingerprint"]
    assert (
        client.post(
            f"/api/tasks/{task['id']}/approve",
            headers=h["alice"],
            json={"expected_fingerprint": task["approval_fingerprint"]},
        ).status_code
        == 409
    )


def test_unavailable_revision_keeps_feedback_and_blocks_old_approval(accounts):
    client, h, _, _ = accounts
    task = propose(accounts)
    response = client.post(
        f"/api/tasks/{task['id']}/request-changes",
        headers=h["alice"],
        json={"owner_feedback": "Lower the amount"},
    )
    assert response.status_code == 200
    assert (
        response.json()["status"] == "needs_changes"
        and response.json()["revision_error"]
    )
    assert response.json()["payload"] == task["payload"]
    assert (
        client.post(f"/api/tasks/{task['id']}/approve", headers=h["alice"]).status_code
        == 409
    )


def test_identical_model_output_is_not_presented_as_a_revision(accounts, monkeypatch):
    client, h, _, _ = accounts
    task = propose(accounts)
    reviser(monkeypatch, task["payload"])
    response = client.post(
        f"/api/tasks/{task['id']}/request-changes",
        headers=h["alice"],
        json={"owner_feedback": "Lower to 400"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "needs_changes"
    assert "unchanged" in response.json()["revision_error"].lower()


def test_blank_feedback_and_wrong_owner_are_rejected(accounts):
    client, h, _, _ = accounts
    task = propose(accounts)
    assert (
        client.post(
            f"/api/tasks/{task['id']}/request-changes",
            headers=h["alice"],
            json={"owner_feedback": " "},
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/tasks/{task['id']}/request-changes",
            headers=h["bob"],
            json={"owner_feedback": "Lower"},
        ).status_code
        == 403
    )


def test_revised_work_never_auto_executes_even_when_agent_mode_is_auto(
    accounts, monkeypatch
):
    client, h, b, _ = accounts
    task = propose(accounts)
    client.put(
        f"/api/businesses/{b}/agents/finance/mode",
        headers=h["alice"],
        json={"mode": "auto", "auto_thresholds": {"auto_approve_max": 10000}},
    )

    async def generate(task, feedback):
        return {"amount": 400.0, "department": "General"}

    monkeypatch.setattr("app.services.task_revision.generate_revision", generate)
    response = client.post(
        f"/api/tasks/{task['id']}/request-changes",
        headers=h["alice"],
        json={"owner_feedback": "Lower to 400"},
    )
    assert response.status_code == 200
    assert (
        response.json()["status"] == "pending_approval"
        and response.json()["executed_at"] is None
    )


def test_revision_does_not_overwrite_a_concurrent_rejection(accounts, monkeypatch):
    client, h, _, _ = accounts
    task = propose(accounts)

    async def generate(current, feedback):
        await client.app.state.db["tasks"].update_one(
            {"task_id": task["id"]}, {"$set": {"status": "rejected"}}
        )
        return {"amount": 400.0, "department": "General"}

    monkeypatch.setattr("app.services.task_revision.generate_revision", generate)
    response = client.post(
        f"/api/tasks/{task['id']}/request-changes",
        headers=h["alice"],
        json={"owner_feedback": "Lower to 400"},
    )
    assert response.status_code == 409
    saved = client.get(f"/api/tasks/{task['id']}", headers=h["alice"]).json()
    assert saved["status"] == "rejected" and saved["payload"] == task["payload"]


def test_typed_model_receives_feedback_and_saves_revised_payload(accounts, monkeypatch):
    client, h, _, _ = accounts
    task = propose(accounts)
    reviser(monkeypatch, {"amount": 400, "department": "General"})
    response = client.post(
        f"/api/tasks/{task['id']}/request-changes",
        headers=h["alice"],
        json={"owner_feedback": "Lower to 400"},
    )
    assert response.status_code == 200
    assert response.json()["payload"]["amount"] == 400
    assert response.json()["status"] == "pending_approval"


@pytest.mark.parametrize(
    "proposal", [{"amount": -1}, {"amount": 400, "unexpected": True}]
)
def test_invalid_revision_is_blocked_without_replacing_payload(
    accounts, monkeypatch, proposal
):
    client, h, _, _ = accounts
    task = propose(accounts)
    reviser(monkeypatch, proposal)
    response = client.post(
        f"/api/tasks/{task['id']}/request-changes",
        headers=h["alice"],
        json={"owner_feedback": "Lower to 400"},
    )
    assert response.status_code == 200
    assert response.json()["payload"] == task["payload"]
    assert (
        response.json()["revision_error"]
        and response.json()["status"] == "needs_changes"
    )


def test_manual_revision_cannot_resubmit_the_unchanged_proposal(accounts):
    client, h, _, _ = accounts
    task = propose(accounts)
    response = client.post(
        f"/api/tasks/{task['id']}/revise",
        headers=h["alice"],
        json={"payload": task["payload"]},
    )
    assert response.status_code == 422


def test_later_ceo_retry_cannot_auto_execute_an_owner_revision(accounts, monkeypatch):
    import asyncio

    client, h, b, _ = accounts
    task = propose(accounts)
    client.put(
        f"/api/businesses/{b}/agents/finance/mode",
        headers=h["alice"],
        json={"mode": "auto", "auto_thresholds": {"auto_approve_max": 10000}},
    )

    async def generate(current, feedback):
        return {"amount": 400.0, "department": "General"}

    monkeypatch.setattr("app.services.task_revision.generate_revision", generate)
    response = client.post(
        f"/api/tasks/{task['id']}/request-changes",
        headers=h["alice"],
        json={"owner_feedback": "Lower to 400"},
    )
    assert response.json()["status"] == "pending_approval"
    # An interrupted/unavailable CEO review can be retried in a later request.
    asyncio.run(
        client.app.state.db["tasks"].update_one(
            {"task_id": task["id"]},
            {"$set": {"status": "pending_ceo_review", "ceo_authorized": False}},
        )
    )
    retried = client.post(f"/api/tasks/{task['id']}/ceo-review", headers=h["alice"])
    assert retried.status_code == 200
    assert retried.json()["status"] == "pending_approval"
    assert retried.json()["executed_at"] is None
