"""Test business/onboarding routes (Addendum Phase 2)"""
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


def _register_and_login(client, email):
    client.post("/api/auth/register", json={"email": email, "password": "supersecret123"})
    login = client.post("/api/auth/login", json={"email": email, "password": "supersecret123"})
    return login.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


class TestCreateAndListBusinesses:
    def test_create_business_uses_defaults_when_omitted(self, client):
        token = _auth_headers(_register_and_login(client, "biz1@example.com"))
        response = client.post(
            "/api/businesses",
            json={"company_name": "Acme Inc", "industry": "Widgets"},
            headers=token,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["starting_budget"] == 100000.0
        assert body["starting_customer_base"] == 1000
        assert body["starting_headcount"] == 50
        assert body["starting_resources"] == 10000
        assert "id" in body

    def test_create_business_respects_custom_values(self, client):
        token = _auth_headers(_register_and_login(client, "biz2@example.com"))
        response = client.post(
            "/api/businesses",
            json={
                "company_name": "Custom Co",
                "industry": "SaaS",
                "starting_budget": 5000,
                "starting_customer_base": 10,
                "starting_headcount": 2,
                "starting_resources": 100,
            },
            headers=token,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["starting_budget"] == 5000
        assert body["starting_customer_base"] == 10

    def test_list_returns_only_my_businesses(self, client):
        token_a = _auth_headers(_register_and_login(client, "usera@example.com"))
        token_b = _auth_headers(_register_and_login(client, "userb@example.com"))

        client.post("/api/businesses", json={"company_name": "A1", "industry": "X"}, headers=token_a)
        client.post("/api/businesses", json={"company_name": "A2", "industry": "X"}, headers=token_a)
        client.post("/api/businesses", json={"company_name": "B1", "industry": "X"}, headers=token_b)

        response_a = client.get("/api/businesses", headers=token_a)
        assert response_a.status_code == 200
        assert len(response_a.json()) == 2

        response_b = client.get("/api/businesses", headers=token_b)
        assert response_b.status_code == 200
        assert len(response_b.json()) == 1

    def test_create_business_requires_auth(self, client):
        response = client.post("/api/businesses", json={"company_name": "NoAuth", "industry": "X"})
        assert response.status_code == 401


class TestGetBusiness:
    def test_owner_can_fetch_their_business(self, client):
        token = _auth_headers(_register_and_login(client, "owner@example.com"))
        create = client.post(
            "/api/businesses", json={"company_name": "Owned Co", "industry": "X"}, headers=token
        )
        business_id = create.json()["id"]

        response = client.get(f"/api/businesses/{business_id}", headers=token)
        assert response.status_code == 200
        assert response.json()["company_name"] == "Owned Co"

    def test_non_owner_gets_403(self, client):
        owner_token = _auth_headers(_register_and_login(client, "owner2@example.com"))
        other_token = _auth_headers(_register_and_login(client, "other@example.com"))

        create = client.post(
            "/api/businesses", json={"company_name": "Private Co", "industry": "X"}, headers=owner_token
        )
        business_id = create.json()["id"]

        response = client.get(f"/api/businesses/{business_id}", headers=other_token)
        assert response.status_code == 403

    def test_unknown_business_404s(self, client):
        token = _auth_headers(_register_and_login(client, "seeker@example.com"))
        response = client.get("/api/businesses/does-not-exist", headers=token)
        assert response.status_code == 404
