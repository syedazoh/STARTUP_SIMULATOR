"""Command-center detail and decisions keep owner guards and preview binding."""

import asyncio
import pytest
from tests.test_account_isolation import accounts  # noqa: F401


def proposal(accounts):
    client, headers, a, _ = accounts
    result = client.post(
        f"/api/businesses/{a}/agents/finance/actions/budget-request",
        headers=headers["alice"],
        json={"amount": 25},
    )
    assert result.status_code == 200
    return result.json()


def test_task_detail_uses_business_ownership(accounts):
    client, headers, _, _ = accounts
    task = proposal(accounts)
    url = "/api/tasks/" + task["id"]
    detail = client.get(url, headers=headers["alice"])
    assert detail.status_code == 200
    assert detail.json()["payload"]["amount"] == 25
    assert len(detail.json()["approval_fingerprint"]) == 64
    assert client.get(url, headers=headers["bob"]).status_code == 403
    assert client.get(url).status_code == 401


@pytest.mark.parametrize("decision", ["approve", "reject"])
def test_stale_displayed_proposal_cannot_be_decided(accounts, decision):
    client, headers, a, _ = accounts
    task = proposal(accounts)
    asyncio.run(
        client.app.state.db["tasks"].update_one(
            {"task_id": task["id"]}, {"$set": {"payload.amount": 1000}}
        )
    )
    response = client.post(
        f"/api/tasks/{task['id']}/{decision}",
        headers=headers["alice"],
        json={"expected_fingerprint": task["approval_fingerprint"]},
    )
    assert response.status_code == 409
    saved = client.get(f"/api/businesses/{a}/tasks", headers=headers["alice"]).json()[0]
    assert saved["status"] == "pending_approval" and saved["result"] is None


def test_matching_preview_can_be_approved_and_replay_is_conflict(accounts):
    client, headers, _, _ = accounts
    task = proposal(accounts)
    url = f"/api/tasks/{task['id']}/approve"
    payload = {"expected_fingerprint": task["approval_fingerprint"]}
    response = client.post(url, headers=headers["alice"], json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "executed"
    assert client.post(url, headers=headers["alice"], json=payload).status_code == 409


@pytest.mark.parametrize("decision", ["approve", "reject"])
def test_edit_between_lookup_and_decision_write_is_not_approved(
    accounts, monkeypatch, decision
):
    client, headers, a, _ = accounts
    task = proposal(accounts)
    from mongomock.collection import Collection

    original = Collection.find_one_and_update
    injected = []

    def racing_update(self, query, update, **kwargs):
        if self.name == "tasks" and update.get("$set", {}).get("status") in {
            "approved",
            "rejected",
        }:
            injected.append(True)
            self.update_one({"task_id": task["id"]}, {"$set": {"payload.amount": 900}})
        return original(self, query, update, **kwargs)

    monkeypatch.setattr(Collection, "find_one_and_update", racing_update)
    response = client.post(
        f"/api/tasks/{task['id']}/{decision}",
        headers=headers["alice"],
        json={"expected_fingerprint": task["approval_fingerprint"]},
    )
    assert injected
    assert response.status_code == 409
    saved = client.get(f"/api/businesses/{a}/tasks", headers=headers["alice"]).json()[0]
    assert saved["status"] == "pending_approval"
    assert saved["result"] is None and saved["payload"]["amount"] == 900
