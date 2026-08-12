"""Test authentication routes (Addendum Phase 1)"""
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


class TestRegister:
    def test_register_returns_user(self, client):
        response = client.post(
            "/api/auth/register", json={"email": "founder@example.com", "password": "supersecret123"}
        )
        assert response.status_code == 201
        body = response.json()
        assert body["email"] == "founder@example.com"
        assert "id" in body
        assert "password" not in body and "hashed_password" not in body

    def test_register_defaults_role_to_owner(self, client):
        response = client.post(
            "/api/auth/register", json={"email": "roledefault@example.com", "password": "supersecret123"}
        )
        assert response.json()["role"] == "owner"

    def test_register_duplicate_email_conflicts(self, client):
        client.post("/api/auth/register", json={"email": "dup@example.com", "password": "supersecret123"})
        response = client.post(
            "/api/auth/register", json={"email": "dup@example.com", "password": "anotherpassword"}
        )
        assert response.status_code == 409

    def test_register_email_is_case_insensitive_for_uniqueness(self, client):
        client.post("/api/auth/register", json={"email": "Case@Example.com", "password": "supersecret123"})
        response = client.post(
            "/api/auth/register", json={"email": "case@example.com", "password": "anotherpassword"}
        )
        assert response.status_code == 409

    def test_register_rejects_short_password(self, client):
        response = client.post(
            "/api/auth/register", json={"email": "short@example.com", "password": "short"}
        )
        assert response.status_code == 422


class TestLogin:
    def test_login_with_correct_credentials(self, client):
        client.post("/api/auth/register", json={"email": "login@example.com", "password": "supersecret123"})
        response = client.post(
            "/api/auth/login", json={"email": "login@example.com", "password": "supersecret123"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        assert len(body["access_token"]) > 20

    def test_login_wrong_password_unauthorized(self, client):
        client.post("/api/auth/register", json={"email": "wrongpw@example.com", "password": "supersecret123"})
        response = client.post(
            "/api/auth/login", json={"email": "wrongpw@example.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401

    def test_login_unknown_email_unauthorized(self, client):
        response = client.post(
            "/api/auth/login", json={"email": "nobody@example.com", "password": "supersecret123"}
        )
        assert response.status_code == 401


class TestMe:
    def test_me_without_token_unauthorized(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_with_valid_token(self, client):
        client.post("/api/auth/register", json={"email": "me@example.com", "password": "supersecret123"})
        login_response = client.post(
            "/api/auth/login", json={"email": "me@example.com", "password": "supersecret123"}
        )
        token = login_response.json()["access_token"]

        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["email"] == "me@example.com"

    def test_me_with_garbage_token_unauthorized(self, client):
        response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
        assert response.status_code == 401

    def test_me_reports_owner_role(self, client):
        client.post("/api/auth/register", json={"email": "role@example.com", "password": "supersecret123"})
        login_response = client.post(
            "/api/auth/login", json={"email": "role@example.com", "password": "supersecret123"}
        )
        token = login_response.json()["access_token"]

        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.json()["role"] == "owner"


class TestRequireAdmin:
    @pytest.mark.asyncio
    async def test_owner_is_rejected(self):
        from fastapi import HTTPException

        from app.api.deps import require_admin
        from app.models.auth_schemas import UserOut
        from datetime import datetime, timezone

        owner = UserOut(id="u1", email="owner@example.com", role="owner", created_at=datetime.now(timezone.utc))
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(user=owner)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_is_allowed(self):
        from app.api.deps import require_admin
        from app.models.auth_schemas import UserOut
        from datetime import datetime, timezone

        admin = UserOut(id="u2", email="admin@example.com", role="admin", created_at=datetime.now(timezone.utc))
        result = await require_admin(user=admin)
        assert result is admin
