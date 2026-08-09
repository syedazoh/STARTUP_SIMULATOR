"""Test manual per-agent action routes (Addendum Phase 6)"""
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


def _enable_policy(client, headers, business_id, agent_key, **policy):
    client.put(
        f"/api/businesses/{business_id}/agents/{agent_key}/policy",
        json={"enabled": True, **policy},
        headers=headers,
    )


class TestFinanceAction:
    def test_manual_budget_request_returns_real_decision(self, client):
        headers = _auth_headers(client, "action1@example.com")
        business_id = _create_business(client, headers)
        _enable_policy(client, headers, business_id, "finance", auto_approve_max=5000)

        response = client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 1000, "department": "Operations"},
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "approved"
        assert "policy_auto_approved" in body["reasoning"]

    def test_manual_action_appears_in_history(self, client):
        headers = _auth_headers(client, "action2@example.com")
        business_id = _create_business(client, headers)
        _enable_policy(client, headers, business_id, "finance", auto_approve_max=5000)

        client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 1000, "department": "Operations"},
            headers=headers,
        )

        history = client.get(
            f"/api/businesses/{business_id}/agents/finance/history", headers=headers
        ).json()
        assert len(history) == 1
        assert history[0]["state"]["budget_pool"] == 99000

    def test_manual_action_appears_in_events_with_manual_source(self, client):
        headers = _auth_headers(client, "action3@example.com")
        business_id = _create_business(client, headers)
        _enable_policy(client, headers, business_id, "finance", auto_approve_max=5000)

        client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 1000, "department": "Operations"},
            headers=headers,
        )

        events = client.get(f"/api/businesses/{business_id}/events", headers=headers).json()
        assert len(events) == 1
        assert events[0]["event_type"] == "budget_request"
        assert events[0]["source"] == "manual"

    def test_manual_action_works_with_no_simulation_running(self, client):
        headers = _auth_headers(client, "action4@example.com")
        business_id = _create_business(client, headers)
        _enable_policy(client, headers, business_id, "finance", auto_deny_min=999999)

        status = client.get(f"/api/businesses/{business_id}/simulation/status", headers=headers).json()
        assert status["is_running"] is False

        response = client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 500, "department": "General"},
            headers=headers,
        )
        assert response.status_code == 200


class TestMarketingAction:
    def test_manual_campaign_launch_cascades_through_negotiation(self, client):
        headers = _auth_headers(client, "action5@example.com")
        business_id = _create_business(client, headers)
        # Policy-gate both ends so the whole cascade stays deterministic and network-free.
        _enable_policy(client, headers, business_id, "marketing", auto_approve_max=100000)
        _enable_policy(client, headers, business_id, "finance", auto_approve_max=100000)

        response = client.post(
            f"/api/businesses/{business_id}/agents/marketing/actions/campaign-launch",
            json={"campaign_name": "Spring Sale", "requested_budget": 3000},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["desired_budget"] == 3000

        events = client.get(f"/api/businesses/{business_id}/events", headers=headers).json()
        event_types = [e["event_type"] for e in events]
        assert event_types == ["campaign_launch", "budget_request", "budget_negotiation"]

        finance = client.get(f"/api/businesses/{business_id}/agents/finance", headers=headers).json()
        assert finance["budget_pool"] == 97000

        marketing = client.get(f"/api/businesses/{business_id}/agents/marketing", headers=headers).json()
        assert marketing["customer_base"] > 1000


class TestHRAndOperationsActions:
    def test_manual_recruitment_request(self, client):
        headers = _auth_headers(client, "action6@example.com")
        business_id = _create_business(client, headers)
        _enable_policy(client, headers, business_id, "hr", auto_approve_max=5)

        response = client.post(
            f"/api/businesses/{business_id}/agents/hr/actions/recruitment-request",
            json={"role": "Engineer", "headcount": 2},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "approved"

        hr = client.get(f"/api/businesses/{business_id}/agents/hr", headers=headers).json()
        assert hr["employee_count"] == 52

    def test_manual_resource_request(self, client):
        headers = _auth_headers(client, "action7@example.com")
        business_id = _create_business(client, headers)
        _enable_policy(client, headers, business_id, "operations", auto_approve_max=5000)

        response = client.post(
            f"/api/businesses/{business_id}/agents/operations/actions/resource-request",
            json={"resource_type": "Cloud Compute", "quantity": 200},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "approved"

        operations = client.get(f"/api/businesses/{business_id}/agents/operations", headers=headers).json()
        assert operations["resource_pool"] == 9800
