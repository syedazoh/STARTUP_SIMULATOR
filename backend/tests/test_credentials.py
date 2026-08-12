"""Test the credential vault: crypto round-trip, connect/list/revoke routes,
and the boundary that no route ever returns a decrypted or encrypted secret
(Phase 3 addendum)."""
import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

import app.database.mongodb as mongodb_module
from app.core.crypto import (
    decrypt_data_key,
    decrypt_with_data_key,
    encrypt_data_key,
    encrypt_with_data_key,
    generate_data_key,
)
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


class TestCryptoRoundTrip:
    def test_data_key_round_trips_through_master_key(self):
        data_key = generate_data_key()
        encrypted = encrypt_data_key(data_key)
        assert encrypted != data_key.decode()
        assert decrypt_data_key(encrypted) == data_key

    def test_payload_round_trips_through_data_key(self):
        data_key = generate_data_key()
        ciphertext = encrypt_with_data_key(data_key, "super-secret-token")
        assert "super-secret-token" not in ciphertext
        assert decrypt_with_data_key(data_key, ciphertext) == "super-secret-token"


class TestConnectListRevoke:
    def test_connect_returns_no_secret_material(self, client):
        headers = _auth_headers(client, "cred1@example.com")
        business_id = _create_business(client, headers)

        response = client.post(
            f"/api/businesses/{business_id}/credentials/instagram/connect",
            json={"access_token": "ig-secret-token-abc123", "scopes": ["basic"]},
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["provider"] == "instagram"
        assert "ig-secret-token-abc123" not in response.text
        assert "access_token" not in body
        assert "encrypted_payload" not in body

    def test_connected_credential_appears_in_list_without_secret(self, client):
        headers = _auth_headers(client, "cred2@example.com")
        business_id = _create_business(client, headers)
        client.post(
            f"/api/businesses/{business_id}/credentials/instagram/connect",
            json={"access_token": "ig-secret-token-xyz", "scopes": []},
            headers=headers,
        )

        response = client.get(f"/api/businesses/{business_id}/credentials", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["provider"] == "instagram"
        assert "ig-secret-token-xyz" not in response.text

    def test_unsupported_provider_rejected(self, client):
        headers = _auth_headers(client, "cred3@example.com")
        business_id = _create_business(client, headers)

        response = client.post(
            f"/api/businesses/{business_id}/credentials/tiktok/connect",
            json={"access_token": "whatever"},
            headers=headers,
        )
        assert response.status_code == 404

    def test_revoke_removes_credential(self, client):
        headers = _auth_headers(client, "cred4@example.com")
        business_id = _create_business(client, headers)
        client.post(
            f"/api/businesses/{business_id}/credentials/instagram/connect",
            json={"access_token": "ig-secret-token", "scopes": []},
            headers=headers,
        )

        delete_response = client.delete(f"/api/businesses/{business_id}/credentials/instagram", headers=headers)
        assert delete_response.status_code == 204

        response = client.get(f"/api/businesses/{business_id}/credentials", headers=headers)
        assert response.json() == []

    def test_revoke_nonexistent_credential_is_404(self, client):
        headers = _auth_headers(client, "cred5@example.com")
        business_id = _create_business(client, headers)

        response = client.delete(f"/api/businesses/{business_id}/credentials/instagram", headers=headers)
        assert response.status_code == 404

    def test_cannot_manage_another_users_credentials(self, client):
        owner_headers = _auth_headers(client, "credowner@example.com")
        business_id = _create_business(client, owner_headers)

        intruder_headers = _auth_headers(client, "credintruder@example.com")
        response = client.get(f"/api/businesses/{business_id}/credentials", headers=intruder_headers)
        assert response.status_code == 403


class TestInstagramPostTaskFlow:
    def test_without_credential_task_executes_but_reports_failure(self, client):
        headers = _auth_headers(client, "ig1@example.com")
        business_id = _create_business(client, headers)

        create_response = client.post(
            f"/api/businesses/{business_id}/agents/marketing/actions/instagram-post",
            json={"content": "hello world"},
            headers=headers,
        )
        task_id = create_response.json()["id"]
        assert create_response.json()["status"] == "pending_approval"

        approve_response = client.post(f"/api/tasks/{task_id}/approve", headers=headers)
        assert approve_response.status_code == 200
        assert approve_response.json()["result"]["status"] == "failed"
        assert approve_response.json()["result"]["reason"] == "no_instagram_credential_connected"

    def test_with_credential_task_executes_and_posts_without_leaking_token(self, client):
        headers = _auth_headers(client, "ig2@example.com")
        business_id = _create_business(client, headers)
        client.post(
            f"/api/businesses/{business_id}/credentials/instagram/connect",
            json={"access_token": "ig-secret-token-999", "scopes": []},
            headers=headers,
        )

        create_response = client.post(
            f"/api/businesses/{business_id}/agents/marketing/actions/instagram-post",
            json={"content": "launching our new feature today"},
            headers=headers,
        )
        task_id = create_response.json()["id"]

        approve_response = client.post(f"/api/tasks/{task_id}/approve", headers=headers)
        assert approve_response.status_code == 200
        body = approve_response.json()
        assert body["status"] == "executed"
        assert body["result"]["status"] == "posted"
        assert "ig-secret-token-999" not in approve_response.text

    def test_instagram_post_always_pending_even_in_auto_mode(self, client):
        """No dominant scalar exists for a social post, so auto mode's
        threshold check can never qualify it — it should always land in the
        queue regardless of the agent's mode."""
        headers = _auth_headers(client, "ig3@example.com")
        business_id = _create_business(client, headers)
        client.put(
            f"/api/businesses/{business_id}/agents/marketing/mode",
            json={"mode": "auto", "auto_thresholds": {"auto_approve_max": 999999}},
            headers=headers,
        )

        response = client.post(
            f"/api/businesses/{business_id}/agents/marketing/actions/instagram-post",
            json={"content": "still needs a human"},
            headers=headers,
        )
        assert response.json()["status"] == "pending_approval"
