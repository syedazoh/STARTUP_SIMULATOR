"""Regression tests for the event-type allowlist (routes/events.py's
PUBLISHABLE_EVENT_TYPES): a client can publish the same event types the
manual action endpoints and simulation event generator use, but not the
internal agent-to-agent negotiation/arbitration events."""
import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

import app.database.mongodb as mongodb_module
from app.api.routes.events import PUBLISHABLE_EVENT_TYPES
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


class TestInternalEventTypesRejected:
    @pytest.mark.parametrize("event_type", ["arbitration_result", "arbitration_request", "budget_negotiation"])
    def test_publishing_an_internal_event_type_returns_400(self, client, event_type):
        headers = _auth_headers(client, f"events-internal-{event_type}@example.com")
        business_id = _create_business(client, headers)

        response = client.post(
            f"/api/businesses/{business_id}/events",
            json={"event_type": event_type, "data": {}},
            headers=headers,
        )
        assert response.status_code == 400


class TestPublishableEventTypesRoundTrip:
    @pytest.mark.parametrize("event_type", sorted(PUBLISHABLE_EVENT_TYPES))
    def test_allowlisted_event_type_publishes_successfully(self, client, event_type):
        headers = _auth_headers(client, f"events-ok-{event_type}@example.com")
        business_id = _create_business(client, headers)

        response = client.post(
            f"/api/businesses/{business_id}/events",
            json={"event_type": event_type, "data": {}},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json() == {"status": "published", "event_type": event_type}

        events = client.get(f"/api/businesses/{business_id}/events", headers=headers).json()
        assert any(e["event_type"] == event_type for e in events)
