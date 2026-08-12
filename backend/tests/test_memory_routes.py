"""Test the memory-inspector API route (Phase 7 addendum)"""
import shutil
import tempfile

import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

import app.database.mongodb as mongodb_module
from app.config import settings
from app.main import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(mongodb_module, "AsyncIOMotorClient", lambda *a, **kw: AsyncMongoMockClient())
    tmp_dir = tempfile.mkdtemp()
    monkeypatch.setattr(settings, "chroma_persist_dir", tmp_dir)
    # The store is a module-level singleton (rag/store.py's _store_instance) —
    # reset it so each test gets a fresh Chroma client pointed at its own
    # temp dir instead of reusing whatever a previous test already built.
    import app.rag.store as store_module

    monkeypatch.setattr(store_module, "_store_instance", None)
    with TestClient(app) as test_client:
        yield test_client
    shutil.rmtree(tmp_dir, ignore_errors=True)


def _auth_headers(client, email):
    client.post("/api/auth/register", json={"email": email, "password": "supersecret123"})
    login = client.post("/api/auth/login", json={"email": email, "password": "supersecret123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _create_business(client, headers, **overrides):
    payload = {"company_name": "Acme Inc", "industry": "Widgets", **overrides}
    response = client.post("/api/businesses", json=payload, headers=headers)
    return response.json()["id"]


class TestMemoryRoute:
    def test_empty_store_returns_empty_list(self, client):
        headers = _auth_headers(client, "mem1@example.com")
        business_id = _create_business(client, headers)

        response = client.get(f"/api/businesses/{business_id}/agents/finance/memory", headers=headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_unknown_agent_is_404(self, client):
        headers = _auth_headers(client, "mem2@example.com")
        business_id = _create_business(client, headers)

        response = client.get(f"/api/businesses/{business_id}/agents/nonexistent/memory", headers=headers)
        assert response.status_code == 404

    def test_cannot_read_another_users_business_memory(self, client):
        owner_headers = _auth_headers(client, "memowner@example.com")
        business_id = _create_business(client, owner_headers)

        intruder_headers = _auth_headers(client, "memintruder@example.com")
        response = client.get(
            f"/api/businesses/{business_id}/agents/finance/memory", headers=intruder_headers
        )
        assert response.status_code == 403

    def test_browse_and_search_after_a_real_decision(self, client):
        headers = _auth_headers(client, "mem3@example.com")
        business_id = _create_business(client, headers)
        _enable_policy = lambda **policy: client.put(
            f"/api/businesses/{business_id}/agents/finance/policy",
            json={"enabled": True, **policy},
            headers=headers,
        )
        _enable_policy(auto_approve_max=5000)

        create_response = client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 1000, "department": "Operations"},
            headers=headers,
        )
        # Finance's action endpoint is gated by the Phase 2 task pipeline
        # (manual mode by default) — approving is what actually runs the
        # agent's decision and triggers persist_memory.
        client.post(f"/api/tasks/{create_response.json()['id']}/approve", headers=headers)

        browse = client.get(f"/api/businesses/{business_id}/agents/finance/memory", headers=headers)
        assert browse.status_code == 200
        assert len(browse.json()) == 1
        assert browse.json()[0]["distance"] is None

        search = client.get(
            f"/api/businesses/{business_id}/agents/finance/memory",
            params={"query": "Budget request from Operations for $1000"},
            headers=headers,
        )
        assert search.status_code == 200
        assert len(search.json()) == 1
        assert search.json()[0]["distance"] is not None

    def test_different_agents_scoped_to_their_own_memory(self, client):
        headers = _auth_headers(client, "mem4@example.com")
        business_id = _create_business(client, headers)
        client.put(
            f"/api/businesses/{business_id}/agents/finance/policy",
            json={"enabled": True, "auto_approve_max": 5000},
            headers=headers,
        )
        create_response = client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 1000, "department": "Operations"},
            headers=headers,
        )
        client.post(f"/api/tasks/{create_response.json()['id']}/approve", headers=headers)

        finance_memory = client.get(
            f"/api/businesses/{business_id}/agents/finance/memory", headers=headers
        ).json()
        marketing_memory = client.get(
            f"/api/businesses/{business_id}/agents/marketing/memory", headers=headers
        ).json()
        assert len(finance_memory) == 1
        assert marketing_memory == []
