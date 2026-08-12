"""Test admin routes: role gating, aggregate data correctness, and the
explicit guarantee that nothing in the credentials vault is ever reachable
from an admin response (Phase 6 addendum)."""
import asyncio

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


def _promote_to_admin(client, email):
    # No API for this by design (see scripts/promote_admin.py) — tests
    # reach into the DB directly, the same way an operator's script would.
    asyncio.run(
        client.app.state.db["users"].update_one({"email": email.lower()}, {"$set": {"role": "admin"}})
    )


class TestAdminGating:
    def test_owner_gets_403(self, client):
        headers = _auth_headers(client, "owner1@example.com")
        response = client.get("/api/admin/businesses", headers=headers)
        assert response.status_code == 403

    def test_unauthenticated_gets_401(self, client):
        response = client.get("/api/admin/businesses")
        assert response.status_code == 401

    def test_admin_can_access(self, client):
        headers = _auth_headers(client, "admin1@example.com")
        _promote_to_admin(client, "admin1@example.com")
        response = client.get("/api/admin/businesses", headers=headers)
        assert response.status_code == 200


class TestAdminBusinessViews:
    def test_list_includes_owner_email_and_task_counts(self, client):
        owner_headers = _auth_headers(client, "owner2@example.com")
        business_id = _create_business(client, owner_headers)
        client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 1000, "department": "Operations"},
            headers=owner_headers,
        )

        admin_headers = _auth_headers(client, "admin2@example.com")
        _promote_to_admin(client, "admin2@example.com")

        response = client.get("/api/admin/businesses", headers=admin_headers)
        assert response.status_code == 200
        entries = [b for b in response.json() if b["id"] == business_id]
        assert len(entries) == 1
        entry = entries[0]
        assert entry["owner_email"] == "owner2@example.com"
        assert entry["task_count"] == 1
        assert entry["pending_task_count"] == 1
        assert entry["simulation_status"] == "never_run"

    def test_detail_view_includes_decision_and_task_counts(self, client):
        owner_headers = _auth_headers(client, "owner3@example.com")
        business_id = _create_business(client, owner_headers)
        create_response = client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 1000, "department": "Operations"},
            headers=owner_headers,
        )
        task_id = create_response.json()["id"]
        client.post(f"/api/tasks/{task_id}/approve", headers=owner_headers)

        admin_headers = _auth_headers(client, "admin3@example.com")
        _promote_to_admin(client, "admin3@example.com")

        response = client.get(f"/api/admin/businesses/{business_id}", headers=admin_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["owner_email"] == "owner3@example.com"
        assert body["task_status_counts"] == {"executed": 1}
        assert body["decision_count"] == 1

    def test_detail_view_unknown_business_is_404(self, client):
        admin_headers = _auth_headers(client, "admin4@example.com")
        _promote_to_admin(client, "admin4@example.com")

        response = client.get("/api/admin/businesses/does-not-exist", headers=admin_headers)
        assert response.status_code == 404

    def test_system_health_reports_counts(self, client):
        owner_headers = _auth_headers(client, "owner5@example.com")
        _create_business(client, owner_headers)

        admin_headers = _auth_headers(client, "admin5@example.com")
        _promote_to_admin(client, "admin5@example.com")

        response = client.get("/api/admin/system-health", headers=admin_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["business_count"] >= 1
        assert body["user_count"] >= 2
        assert body["mongo_connected"] is True  # mongomock_motor answers the ping successfully too


class TestAdminNeverSeesCredentials:
    def test_connected_credential_secret_never_appears_in_admin_responses(self, client):
        owner_headers = _auth_headers(client, "owner6@example.com")
        business_id = _create_business(client, owner_headers)
        secret_token = "ig-super-secret-token-should-never-leak-777"
        client.post(
            f"/api/businesses/{business_id}/credentials/instagram/connect",
            json={"access_token": secret_token, "scopes": []},
            headers=owner_headers,
        )

        admin_headers = _auth_headers(client, "admin6@example.com")
        _promote_to_admin(client, "admin6@example.com")

        list_response = client.get("/api/admin/businesses", headers=admin_headers)
        detail_response = client.get(f"/api/admin/businesses/{business_id}", headers=admin_headers)
        health_response = client.get("/api/admin/system-health", headers=admin_headers)

        assert secret_token not in list_response.text
        assert secret_token not in detail_response.text
        assert secret_token not in health_response.text

        # Also confirm the admin module never actually imported the vault's
        # decrypt function at all — checking the real namespace, not just
        # grepping source text (which would also match this very docstring).
        import app.api.routes.admin as admin_module
        import app.services.credentials as credentials_module

        assert credentials_module.get_decrypted_token not in vars(admin_module).values()
        assert "credentials" not in admin_module.router.prefix
