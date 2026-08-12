"""Test the task/approval pipeline, wired end-to-end through Finance's
budget-request endpoint (Phase 2 reference implementation)."""
import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

import app.database.mongodb as mongodb_module
from app.main import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(mongodb_module, "AsyncIOMotorClient", lambda *a, **kw: AsyncMongoMockClient())
    with TestClient(app) as test_client:
        yield test_client


def _auth_headers(client, email):
    client.post("/api/auth/register", json={"email": email, "password": "supersecret123"})
    login = client.post("/api/auth/login", json={"email": email, "password": "supersecret123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _create_business(client, headers, **overrides):
    payload = {"company_name": "Acme Inc", "industry": "Widgets", **overrides}
    response = client.post("/api/businesses", json=payload, headers=headers)
    return response.json()["id"]


def _budget_pool(client, headers, business_id):
    return client.get(f"/api/businesses/{business_id}/agents/finance", headers=headers).json()["budget_pool"]


class TestManualModeCreatesTask:
    def test_budget_request_lands_pending_approval_without_touching_budget(self, client):
        headers = _auth_headers(client, "task1@example.com")
        business_id = _create_business(client, headers)
        starting_pool = _budget_pool(client, headers, business_id)

        response = client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 1000, "department": "Operations"},
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "pending_approval"
        assert body["result"] is None
        assert _budget_pool(client, headers, business_id) == starting_pool

    def test_task_appears_in_business_task_queue(self, client):
        headers = _auth_headers(client, "task2@example.com")
        business_id = _create_business(client, headers)
        client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 1000, "department": "Operations"},
            headers=headers,
        )

        response = client.get(
            f"/api/businesses/{business_id}/tasks", params={"task_status": "pending_approval"}, headers=headers
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["action_type"] == "budget_request"


class TestApprove:
    def test_approve_executes_and_updates_budget(self, client):
        headers = _auth_headers(client, "task3@example.com")
        business_id = _create_business(client, headers)
        starting_pool = _budget_pool(client, headers, business_id)

        create_response = client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 1000, "department": "Operations"},
            headers=headers,
        )
        task_id = create_response.json()["id"]

        approve_response = client.post(f"/api/tasks/{task_id}/approve", headers=headers)
        assert approve_response.status_code == 200
        body = approve_response.json()
        assert body["status"] == "executed"
        assert body["result"]["status"] == "approved"
        assert _budget_pool(client, headers, business_id) == starting_pool - 1000

    def test_approving_already_executed_task_conflicts(self, client):
        headers = _auth_headers(client, "task4@example.com")
        business_id = _create_business(client, headers)
        create_response = client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 1000, "department": "Operations"},
            headers=headers,
        )
        task_id = create_response.json()["id"]
        client.post(f"/api/tasks/{task_id}/approve", headers=headers)

        response = client.post(f"/api/tasks/{task_id}/approve", headers=headers)
        assert response.status_code == 409


class TestReject:
    def test_reject_leaves_budget_untouched_and_stores_feedback(self, client):
        headers = _auth_headers(client, "task5@example.com")
        business_id = _create_business(client, headers)
        starting_pool = _budget_pool(client, headers, business_id)

        create_response = client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 1000, "department": "Operations"},
            headers=headers,
        )
        task_id = create_response.json()["id"]

        response = client.post(
            f"/api/tasks/{task_id}/reject", json={"owner_feedback": "too much"}, headers=headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "rejected"
        assert response.json()["owner_feedback"] == "too much"
        assert _budget_pool(client, headers, business_id) == starting_pool


class TestRequestChanges:
    def test_request_changes_sets_needs_changes_and_is_decidable_again(self, client):
        headers = _auth_headers(client, "task6@example.com")
        business_id = _create_business(client, headers)
        create_response = client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 1000, "department": "Operations"},
            headers=headers,
        )
        task_id = create_response.json()["id"]

        response = client.post(
            f"/api/tasks/{task_id}/request-changes",
            json={"owner_feedback": "lower the amount"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "needs_changes"

        approve_response = client.post(f"/api/tasks/{task_id}/approve", headers=headers)
        assert approve_response.status_code == 200
        assert approve_response.json()["status"] == "executed"


class TestAutoMode:
    def test_within_threshold_auto_executes_immediately(self, client):
        headers = _auth_headers(client, "task7@example.com")
        business_id = _create_business(client, headers)
        starting_pool = _budget_pool(client, headers, business_id)

        client.put(
            f"/api/businesses/{business_id}/agents/finance/mode",
            json={"mode": "auto", "auto_thresholds": {"auto_approve_max": 2000}},
            headers=headers,
        )

        response = client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 1000, "department": "Operations"},
            headers=headers,
        )
        body = response.json()
        assert body["status"] == "executed"
        assert body["result"]["status"] == "approved"
        assert _budget_pool(client, headers, business_id) == starting_pool - 1000

    def test_outside_threshold_falls_back_to_pending_approval(self, client):
        headers = _auth_headers(client, "task8@example.com")
        business_id = _create_business(client, headers)
        starting_pool = _budget_pool(client, headers, business_id)

        client.put(
            f"/api/businesses/{business_id}/agents/finance/mode",
            json={"mode": "auto", "auto_thresholds": {"auto_approve_max": 500}},
            headers=headers,
        )

        response = client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 1000, "department": "Operations"},
            headers=headers,
        )
        assert response.json()["status"] == "pending_approval"
        assert _budget_pool(client, headers, business_id) == starting_pool


class TestOwnership:
    def test_cannot_approve_another_users_task(self, client):
        owner_headers = _auth_headers(client, "taskowner@example.com")
        business_id = _create_business(client, owner_headers)
        create_response = client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 1000, "department": "Operations"},
            headers=owner_headers,
        )
        task_id = create_response.json()["id"]

        intruder_headers = _auth_headers(client, "taskintruder@example.com")
        response = client.post(f"/api/tasks/{task_id}/approve", headers=intruder_headers)
        assert response.status_code == 403

    def test_approve_requires_auth(self, client):
        response = client.post("/api/tasks/some-id/approve")
        assert response.status_code == 401

    def test_approve_unknown_task_is_404(self, client):
        headers = _auth_headers(client, "task9@example.com")
        response = client.post("/api/tasks/does-not-exist/approve", headers=headers)
        assert response.status_code == 404
