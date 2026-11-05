"""Two verified Supabase identities exercise actual API authorization guards."""

from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

import app.database.mongodb as mongodb_module
from app.main import app


@pytest.fixture
def accounts(monkeypatch):
    monkeypatch.setattr(
        mongodb_module, "AsyncIOMotorClient", lambda *a, **kw: AsyncMongoMockClient()
    )
    identities = {
        name: (str(uuid4()), f"{name}@example.com") for name in ("alice", "bob")
    }

    async def verify(token):
        if token not in identities:
            raise HTTPException(401, "Invalid session")
        return identities[token]

    monkeypatch.setattr("app.services.supabase_auth.verify_identity", verify)
    with TestClient(app) as client:
        headers = {
            name: {"Authorization": f"Bearer {name}", "X-Auth-Provider": "supabase"}
            for name in identities
        }
        a = client.post(
            "/api/businesses",
            headers=headers["alice"],
            json={"company_name": "Alice private", "industry": "Software"},
        )
        b = client.post(
            "/api/businesses",
            headers=headers["bob"],
            json={"company_name": "Bob private", "industry": "Software"},
        )
        assert a.status_code == b.status_code == 201
        yield client, headers, a.json()["id"], b.json()["id"]


def test_two_accounts_have_separate_lists(accounts):
    client, headers, a, b = accounts
    assert [
        x["id"] for x in client.get("/api/businesses", headers=headers["alice"]).json()
    ] == [a]
    assert [
        x["id"] for x in client.get("/api/businesses", headers=headers["bob"]).json()
    ] == [b]


@pytest.mark.parametrize(
    "suffix",
    [
        "",
        "/agents",
        "/tasks",
        "/profile",
        "/credentials",
        "/ceo/plans",
        "/ceo/reports",
        "/finances",
        "/agents/finance/history",
        "/agents/finance/memory",
    ],
)
def test_known_business_id_does_not_grant_read_access(accounts, suffix):
    client, headers, a, _ = accounts
    assert (
        client.get(f"/api/businesses/{a}{suffix}", headers=headers["bob"]).status_code
        == 403
    )


def test_other_account_cannot_create_work_or_spoof_business_owner(accounts):
    client, headers, a, b = accounts
    denied = client.post(
        f"/api/businesses/{a}/agents/finance/actions/budget-request",
        headers=headers["bob"],
        json={"amount": 1},
    )
    assert denied.status_code == 403
    assert (
        client.get(f"/api/businesses/{a}/tasks", headers=headers["alice"]).json() == []
    )
    created = client.post(
        "/api/businesses",
        headers=headers["bob"],
        json={
            "company_name": "Spoof attempt",
            "industry": "Software",
            "owner_user_id": "alice",
        },
    )
    assert created.status_code == 201
    assert (
        created.json()["owner_user_id"]
        == client.get("/api/auth/me", headers=headers["bob"]).json()["id"]
    )


@pytest.mark.parametrize(
    "action,payload",
    [
        ("approve", None),
        ("reject", {}),
        ("request-changes", {}),
        ("revise", {"payload": {"amount": 2}}),
        ("ceo-review", None),
        ("release-budget", None),
    ],
)
def test_task_id_cannot_be_used_to_mutate_other_business(accounts, action, payload):
    client, headers, a, _ = accounts
    created = client.post(
        f"/api/businesses/{a}/agents/finance/actions/budget-request",
        headers=headers["alice"],
        json={"amount": 1},
    )
    assert created.status_code == 200
    tid = created.json()["id"]
    before = client.get(f"/api/businesses/{a}/tasks", headers=headers["alice"]).json()
    assert (
        client.post(
            f"/api/tasks/{tid}/{action}", headers=headers["bob"], json=payload
        ).status_code
        == 403
    )
    assert (
        client.get(f"/api/businesses/{a}/tasks", headers=headers["alice"]).json()
        == before
    )


def test_unverified_or_missing_session_cannot_read_business(accounts):
    client, _, a, _ = accounts
    assert client.get(f"/api/businesses/{a}").status_code == 401
    assert (
        client.get(
            f"/api/businesses/{a}",
            headers={"Authorization": "Bearer invalid", "X-Auth-Provider": "supabase"},
        ).status_code
        == 401
    )
