"""Test agent execution mode routes (Phase 2 addendum)"""
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


class TestAgentModeRoutes:
    def test_get_mode_defaults_to_manual(self, client):
        headers = _auth_headers(client, "mode1@example.com")
        business_id = _create_business(client, headers)

        response = client.get(f"/api/businesses/{business_id}/agents/finance/mode", headers=headers)
        assert response.status_code == 200
        assert response.json()["mode"] == "manual"

    def test_put_mode_updates_and_persists(self, client):
        headers = _auth_headers(client, "mode2@example.com")
        business_id = _create_business(client, headers)

        put_response = client.put(
            f"/api/businesses/{business_id}/agents/finance/mode",
            json={"mode": "auto", "auto_thresholds": {"auto_approve_max": 2000}},
            headers=headers,
        )
        assert put_response.status_code == 200
        assert put_response.json()["mode"] == "auto"
        assert put_response.json()["auto_thresholds"]["auto_approve_max"] == 2000

        get_response = client.get(f"/api/businesses/{business_id}/agents/finance/mode", headers=headers)
        assert get_response.json()["mode"] == "auto"

    def test_ceo_has_no_mode_endpoint(self, client):
        headers = _auth_headers(client, "mode3@example.com")
        business_id = _create_business(client, headers)

        response = client.get(f"/api/businesses/{business_id}/agents/ceo/mode", headers=headers)
        assert response.status_code == 404

    def test_cannot_access_another_users_business_mode(self, client):
        owner_headers = _auth_headers(client, "modeowner@example.com")
        business_id = _create_business(client, owner_headers)

        intruder_headers = _auth_headers(client, "modeintruder@example.com")
        response = client.get(f"/api/businesses/{business_id}/agents/finance/mode", headers=intruder_headers)
        assert response.status_code == 403
