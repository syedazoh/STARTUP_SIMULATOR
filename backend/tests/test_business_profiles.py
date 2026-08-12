"""Test business profile routes (Phase 1 addendum)"""
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


class TestBusinessProfileRoutes:
    def test_get_profile_defaults_to_empty(self, client):
        headers = _auth_headers(client, "profile1@example.com")
        business_id = _create_business(client, headers)

        response = client.get(f"/api/businesses/{business_id}/profile", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["brand"]["voice_tone"] == ""
        assert body["custom_context"] == []

    def test_upsert_profile_persists(self, client):
        headers = _auth_headers(client, "profile2@example.com")
        business_id = _create_business(client, headers)

        payload = {
            "brand": {
                "voice_tone": "playful",
                "mission_statement": "ship fast",
                "target_audience": "gen z",
                "competitors": ["X", "Y"],
            },
            "product": {"description": "widgets", "pricing_model": "subscription", "price_points": [9.99]},
            "marketing": {
                "active_channels": ["instagram"],
                "posting_frequency": "daily",
                "content_dos": ["be bold"],
                "content_donts": ["be boring"],
            },
            "finance": {"monthly_budget_cap": 5000, "currency": "USD", "spend_categories": ["ads"]},
            "operations": {"support_hours": "9-5", "escalation_policy": "escalate after 2h"},
        }
        post_response = client.post(f"/api/businesses/{business_id}/profile", json=payload, headers=headers)
        assert post_response.status_code == 200
        assert post_response.json()["brand"]["voice_tone"] == "playful"

        get_response = client.get(f"/api/businesses/{business_id}/profile", headers=headers)
        assert get_response.json()["finance"]["monthly_budget_cap"] == 5000
        assert get_response.json()["marketing"]["active_channels"] == ["instagram"]

    def test_upsert_twice_overwrites_not_duplicates(self, client):
        headers = _auth_headers(client, "profile3@example.com")
        business_id = _create_business(client, headers)

        client.post(
            f"/api/businesses/{business_id}/profile",
            json={"brand": {"voice_tone": "formal"}},
            headers=headers,
        )
        client.post(
            f"/api/businesses/{business_id}/profile",
            json={"brand": {"voice_tone": "casual"}},
            headers=headers,
        )
        response = client.get(f"/api/businesses/{business_id}/profile", headers=headers)
        assert response.json()["brand"]["voice_tone"] == "casual"

    def test_add_context_note_appends(self, client):
        headers = _auth_headers(client, "profile4@example.com")
        business_id = _create_business(client, headers)

        client.post(
            f"/api/businesses/{business_id}/profile/context",
            json={"label": "launch", "text": "launched Aug 2026"},
            headers=headers,
        )
        response = client.post(
            f"/api/businesses/{business_id}/profile/context",
            json={"label": "pivot", "text": "pivoted to B2B"},
            headers=headers,
        )
        assert response.status_code == 200
        notes = response.json()["custom_context"]
        assert [n["label"] for n in notes] == ["launch", "pivot"]

    def test_context_note_preserves_existing_profile_fields(self, client):
        headers = _auth_headers(client, "profile5@example.com")
        business_id = _create_business(client, headers)

        client.post(
            f"/api/businesses/{business_id}/profile",
            json={"brand": {"voice_tone": "formal"}},
            headers=headers,
        )
        response = client.post(
            f"/api/businesses/{business_id}/profile/context",
            json={"label": "note", "text": "some context"},
            headers=headers,
        )
        assert response.json()["brand"]["voice_tone"] == "formal"

    def test_cannot_access_another_users_business_profile(self, client):
        owner_headers = _auth_headers(client, "profileowner@example.com")
        business_id = _create_business(client, owner_headers)

        intruder_headers = _auth_headers(client, "profileintruder@example.com")
        response = client.get(f"/api/businesses/{business_id}/profile", headers=intruder_headers)
        assert response.status_code == 403

    def test_profile_requires_auth(self, client):
        response = client.get("/api/businesses/some-id/profile")
        assert response.status_code == 401
