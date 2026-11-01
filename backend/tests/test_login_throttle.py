"""Security regressions for the public login budget."""
import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient
from pymongo.errors import ConnectionFailure

from app.api.routes import auth
from app.core import login_throttle
from app.database.mongodb import InMemoryDatabase


@pytest.fixture
def db():
    return AsyncMongoMockClient()["login_throttle_test"]


def make_client(db):
    app = FastAPI()
    app.state.db = db
    app.include_router(auth.router)
    return TestClient(app)


@pytest.fixture
def client(db, monkeypatch):
    # Future time keeps mongomock's wall-clock TTL cleanup from deleting buckets.
    monkeypatch.setattr(login_throttle.time, "time", lambda: 4102444800)
    with make_client(db) as client:
        yield client


def login(client, email="founder@example.com", password="wrongpassword"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


@pytest.mark.parametrize("registered", [False, True])
def test_budget_blocks_before_password_check_and_token_creation(client, monkeypatch, registered, caplog):
    if registered:
        assert client.post("/api/auth/register", json={
            "email": "founder@example.com", "password": "supersecret123",
        }).status_code == 201
    verify = Mock(return_value=False)
    token = Mock()
    monkeypatch.setattr(auth, "verify_password", verify)
    monkeypatch.setattr(auth, "create_access_token", token)
    for _ in range(5):
        assert login(client).status_code == 401
    assert verify.call_count == (5 if registered else 0)
    verify.reset_mock()
    # Even the correct password must not be checked while the budget is exhausted.
    response = login(client, password="supersecret123")
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "300"
    assert "access_token" not in response.json()
    verify.assert_not_called()
    token.assert_not_called()
    assert "Login attempt throttled" in caplog.text
    assert "founder@example.com" not in caplog.text
    assert "supersecret123" not in caplog.text


def test_case_variants_share_budget_and_other_accounts_are_independent(client):
    for email in ["Founder@example.com", "founder@example.com", "FOUNDER@EXAMPLE.COM",
                  "Founder@Example.com", "founder@example.com"]:
        assert login(client, email=email).status_code == 401
    assert login(client, email="FOUNDER@example.com").status_code == 429
    assert login(client, email="other@example.com").status_code == 401


def test_success_does_not_reset_budget(client):
    client.post("/api/auth/register", json={
        "email": "founder@example.com", "password": "supersecret123",
    })
    for _ in range(4):
        assert login(client).status_code == 401
    assert login(client, password="supersecret123").status_code == 200
    assert login(client).status_code == 429


def test_shared_budget_survives_new_app_instance(client, db):
    for _ in range(5):
        assert login(client).status_code == 401
    with make_client(db) as second_client:
        assert login(second_client).status_code == 429


def test_window_expires_without_waiting_for_ttl_cleanup(client, db, monkeypatch):
    for _ in range(5):
        assert login(client).status_code == 401
    monkeypatch.setattr(login_throttle.time, "time", lambda: 4102445099.5)
    response = login(client)
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "1"
    monkeypatch.setattr(login_throttle.time, "time", lambda: 4102445100)
    assert login(client).status_code == 401
    # Old window is still present: TTL deletion isn't required to restore access.
    assert asyncio.run(db["login_attempts"].count_documents({})) == 2


@pytest.mark.asyncio
async def test_concurrent_attempts_share_one_atomic_budget(db, monkeypatch):
    monkeypatch.setattr(login_throttle.time, "time", lambda: 4102444800)
    results = await asyncio.gather(*(
        login_throttle.check_login_attempt(db, "founder@example.com") for _ in range(20)
    ), return_exceptions=True)
    assert results.count(None) == 5
    blocked = [result for result in results if isinstance(result, HTTPException)]
    assert len(blocked) == 15
    assert all(result.status_code == 429 for result in blocked)
    indexes = await db["login_attempts"].index_information()
    assert indexes["expires_at_1"]["expireAfterSeconds"] == 0


@pytest.mark.parametrize("operation", ["create_index", "find_one_and_update"])
def test_storage_failure_blocks_login(client, db, monkeypatch, operation):
    attempts = db["login_attempts"]
    monkeypatch.setattr(attempts, operation, AsyncMock(side_effect=ConnectionFailure()))
    # mongomock-motor wraps the collection anew on each db[name] access.
    monkeypatch.setattr(client.app.state, "db", {"login_attempts": attempts})
    lookup = AsyncMock()
    verify = Mock()
    monkeypatch.setattr(auth, "find_one", lookup)
    monkeypatch.setattr(auth, "verify_password", verify)
    assert login(client).status_code == 503
    lookup.assert_not_called()
    verify.assert_not_called()


def test_in_memory_fallback_cannot_bypass_throttle(monkeypatch):
    verify = Mock()
    monkeypatch.setattr(auth, "verify_password", verify)
    with make_client(InMemoryDatabase()) as client:
        assert login(client).status_code == 503
    verify.assert_not_called()
