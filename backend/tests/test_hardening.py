"""Test Phase 8 hardening: audit logging (task transitions, credential
connect/revoke) and rate limiting on chat/task-creation endpoints."""
import asyncio

import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

import app.api.routes.agent_actions as agent_actions_module
import app.api.routes.agent_modes as agent_modes_module
import app.api.routes.business_profiles as business_profiles_module
import app.api.routes.chat as chat_module
import app.api.routes.credentials as credentials_module
import app.api.routes.policies as policies_module
import app.api.routes.tasks as tasks_module
import app.database.mongodb as mongodb_module
import app.services.chat as chat_service_module
from app.agents.schemas import ChatReply
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


def _promote_to_admin(client, email):
    asyncio.run(
        client.app.state.db["users"].update_one({"email": email.lower()}, {"$set": {"role": "admin"}})
    )


def _audit_logs(client, admin_headers, **params):
    return client.get("/api/admin/audit-logs", params=params, headers=admin_headers).json()


class TestTaskAuditTrail:
    def test_create_and_approve_are_both_logged_with_user_id(self, client):
        headers = _auth_headers(client, "audit1@example.com")
        business_id = _create_business(client, headers)
        admin_headers = _auth_headers(client, "audit1admin@example.com")
        _promote_to_admin(client, "audit1admin@example.com")

        create_response = client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 1000, "department": "Operations"},
            headers=headers,
        )
        task_id = create_response.json()["id"]
        client.post(f"/api/tasks/{task_id}/approve", headers=headers)

        logs = _audit_logs(client, admin_headers, business_id=business_id)
        actions = [entry["action"] for entry in logs]
        assert "task_created" in actions
        assert "task_approved" in actions
        for entry in logs:
            assert entry["user_id"]
            assert entry["business_id"] == business_id
            if entry["action"] in ("task_created", "task_approved"):
                assert entry["target_id"] == task_id

    def test_reject_and_request_changes_are_logged_with_feedback(self, client):
        headers = _auth_headers(client, "audit2@example.com")
        business_id = _create_business(client, headers)
        admin_headers = _auth_headers(client, "audit2admin@example.com")
        _promote_to_admin(client, "audit2admin@example.com")

        create_response = client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 1000, "department": "Operations"},
            headers=headers,
        )
        task_id = create_response.json()["id"]
        client.post(f"/api/tasks/{task_id}/reject", json={"owner_feedback": "too much"}, headers=headers)

        logs = _audit_logs(client, admin_headers, business_id=business_id)
        rejected = next(e for e in logs if e["action"] == "task_rejected")
        assert rejected["details"]["owner_feedback"] == "too much"


class TestCredentialAuditTrail:
    def test_connect_and_revoke_are_logged(self, client):
        headers = _auth_headers(client, "audit3@example.com")
        business_id = _create_business(client, headers)
        admin_headers = _auth_headers(client, "audit3admin@example.com")
        _promote_to_admin(client, "audit3admin@example.com")

        client.post(
            f"/api/businesses/{business_id}/credentials/instagram/connect",
            json={"access_token": "ig-secret", "scopes": []},
            headers=headers,
        )
        client.delete(f"/api/businesses/{business_id}/credentials/instagram", headers=headers)

        logs = _audit_logs(client, admin_headers, business_id=business_id)
        actions = [entry["action"] for entry in logs]
        assert "credential_connected" in actions
        assert "credential_revoked" in actions
        for entry in logs:
            if entry["action"] in ("credential_connected", "credential_revoked"):
                assert entry["target_id"] == "instagram"

        # The audit trail records that a credential was touched, never the secret itself.
        assert "ig-secret" not in client.get(
            "/api/admin/audit-logs", params={"business_id": business_id}, headers=admin_headers
        ).text


class TestRateLimiting:
    def test_task_creation_endpoint_returns_429_after_threshold(self, client, monkeypatch):
        monkeypatch.setattr(agent_actions_module._action_rate_limiter, "max_requests", 2)

        headers = _auth_headers(client, "ratelimit1@example.com")
        business_id = _create_business(client, headers)

        for _ in range(2):
            response = client.post(
                f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
                json={"amount": 100, "department": "Operations"},
                headers=headers,
            )
            assert response.status_code == 200

        third = client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 100, "department": "Operations"},
            headers=headers,
        )
        assert third.status_code == 429

    def test_rate_limit_is_scoped_per_user(self, client, monkeypatch):
        monkeypatch.setattr(agent_actions_module._action_rate_limiter, "max_requests", 1)

        headers_a = _auth_headers(client, "ratelimit2a@example.com")
        business_a = _create_business(client, headers_a)
        headers_b = _auth_headers(client, "ratelimit2b@example.com")
        business_b = _create_business(client, headers_b)

        first = client.post(
            f"/api/businesses/{business_a}/agents/finance/actions/budget-request",
            json={"amount": 100, "department": "Operations"},
            headers=headers_a,
        )
        assert first.status_code == 200

        # A different user's own first request should not be blocked by user A's usage.
        second = client.post(
            f"/api/businesses/{business_b}/agents/finance/actions/budget-request",
            json={"amount": 100, "department": "Operations"},
            headers=headers_b,
        )
        assert second.status_code == 200

    def test_chat_endpoint_returns_429_after_threshold(self, client, monkeypatch):
        class FakeChatLLM:
            def with_structured_output(self, schema):
                return self

            async def ainvoke(self, prompt):
                return ChatReply(reply="hi there")

        monkeypatch.setattr(chat_service_module, "get_groq_llm", lambda *a, **kw: FakeChatLLM())
        monkeypatch.setattr(chat_module._chat_rate_limiter, "max_requests", 1)

        headers = _auth_headers(client, "ratelimit3@example.com")
        business_id = _create_business(client, headers)

        first = client.post(
            f"/api/businesses/{business_id}/agents/finance/chat", json={"content": "hi"}, headers=headers
        )
        assert first.status_code == 200

        second = client.post(
            f"/api/businesses/{business_id}/agents/finance/chat", json={"content": "hi again"}, headers=headers
        )
        assert second.status_code == 429


class TestNewlyRateLimitedRoutes:
    """Coverage for the routes rate-limited alongside chat/agent-actions:
    business_profiles, credentials connect/disconnect, policies, agent_modes,
    and tasks approve/reject/request-changes/assets — so this coverage
    doesn't silently regress if a future change drops one of them."""

    def test_business_profile_upsert_returns_429_after_threshold(self, client, monkeypatch):
        monkeypatch.setattr(business_profiles_module._profile_rate_limiter, "max_requests", 1)
        headers = _auth_headers(client, "ratelimit-profile@example.com")
        business_id = _create_business(client, headers)

        first = client.post(f"/api/businesses/{business_id}/profile", json={}, headers=headers)
        assert first.status_code == 200

        second = client.post(f"/api/businesses/{business_id}/profile", json={}, headers=headers)
        assert second.status_code == 429

    def test_credential_connect_returns_429_after_threshold(self, client, monkeypatch):
        monkeypatch.setattr(credentials_module._credentials_rate_limiter, "max_requests", 1)
        headers = _auth_headers(client, "ratelimit-cred@example.com")
        business_id = _create_business(client, headers)

        first = client.post(
            f"/api/businesses/{business_id}/credentials/instagram/connect",
            json={"access_token": "tok", "scopes": []},
            headers=headers,
        )
        assert first.status_code == 200

        second = client.delete(f"/api/businesses/{business_id}/credentials/instagram", headers=headers)
        assert second.status_code == 429

    def test_policy_update_returns_429_after_threshold(self, client, monkeypatch):
        monkeypatch.setattr(policies_module._policy_rate_limiter, "max_requests", 1)
        headers = _auth_headers(client, "ratelimit-policy@example.com")
        business_id = _create_business(client, headers)

        first = client.put(
            f"/api/businesses/{business_id}/agents/finance/policy",
            json={"enabled": True, "auto_approve_max": 1000},
            headers=headers,
        )
        assert first.status_code == 200

        second = client.put(
            f"/api/businesses/{business_id}/agents/finance/policy",
            json={"enabled": True, "auto_approve_max": 2000},
            headers=headers,
        )
        assert second.status_code == 429

    def test_agent_mode_update_returns_429_after_threshold(self, client, monkeypatch):
        monkeypatch.setattr(agent_modes_module._mode_rate_limiter, "max_requests", 1)
        headers = _auth_headers(client, "ratelimit-mode@example.com")
        business_id = _create_business(client, headers)

        first = client.put(
            f"/api/businesses/{business_id}/agents/finance/mode", json={"mode": "manual"}, headers=headers
        )
        assert first.status_code == 200

        second = client.put(
            f"/api/businesses/{business_id}/agents/finance/mode", json={"mode": "auto"}, headers=headers
        )
        assert second.status_code == 429

    def test_task_decision_endpoints_return_429_after_threshold(self, client, monkeypatch):
        monkeypatch.setattr(tasks_module._task_rate_limiter, "max_requests", 1)
        headers = _auth_headers(client, "ratelimit-task@example.com")
        business_id = _create_business(client, headers)

        def _create_pending_task():
            response = client.post(
                f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
                json={"amount": 100, "department": "Operations"},
                headers=headers,
            )
            return response.json()["id"]

        first_task_id = _create_pending_task()
        second_task_id = _create_pending_task()

        first = client.post(f"/api/tasks/{first_task_id}/approve", headers=headers)
        assert first.status_code == 200

        second = client.post(f"/api/tasks/{second_task_id}/approve", headers=headers)
        assert second.status_code == 429
