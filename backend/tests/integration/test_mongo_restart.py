"""Real Mongo persistence, separate application lifespans, no live AI/Supabase.

Set MONGODB_INTEGRATION_URL to a dedicated test server. Never uses app .env URL.
A random nov45_test_ database is created and only that database is cleaned up.
"""

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.config import settings
from app.main import app


def test_linked_business_and_pending_task_survive_backend_restart(monkeypatch):
    uri = os.environ.get("MONGODB_INTEGRATION_URL")
    if not uri:
        pytest.skip("MONGODB_INTEGRATION_URL is required for real persistence evidence")
    database = "nov45_test_" + uuid4().hex
    control = MongoClient(uri, serverSelectionTimeoutMS=5000)
    control.admin.command("ping")  # An unavailable configured server is a FAILURE.
    monkeypatch.setattr(settings, "mongodb_url", uri)
    monkeypatch.setattr(settings, "mongodb_db_name", database)
    subject = str(uuid4())

    async def verify(token):
        assert token == "controlled-test-token"
        return subject, "restart@example.com"

    monkeypatch.setattr("app.services.supabase_auth.verify_identity", verify)
    supa = {
        "Authorization": "Bearer controlled-test-token",
        "X-Auth-Provider": "supabase",
    }
    try:
        with TestClient(app) as first:
            assert first.get("/health").json()["mongo"] == "connected"
            user = first.post(
                "/api/auth/register",
                json={"email": "restart@example.com", "password": "test-only-password"},
            ).json()
            login = first.post(
                "/api/auth/login",
                json={"email": "restart@example.com", "password": "test-only-password"},
            )
            assert login.status_code == 200
            native = {"Authorization": "Bearer " + login.json()["access_token"]}
            link = first.post(
                "/api/auth/link-supabase",
                headers=native,
                json={"access_token": "controlled-test-token"},
            )
            assert link.status_code == 200
            biz = first.post(
                "/api/businesses",
                headers=supa,
                json={"company_name": "Restart evidence", "industry": "Software"},
            )
            assert biz.status_code == 201
            bid = biz.json()["id"]
            task = first.post(
                f"/api/businesses/{bid}/agents/finance/actions/budget-request",
                headers=supa,
                json={"amount": 25},
            )
            assert (
                task.status_code == 200 and task.json()["status"] == "pending_approval"
            )
            original_key = control[database].users.find_one({"user_id": user["id"]})[
                "encrypted_data_key"
            ]
            first_registry = app.state.agent_registry
        # Reopens the actual Motor connection and constructs a fresh agent registry.
        with TestClient(app) as second:
            assert app.state.agent_registry is not first_registry
            assert second.get("/health").json()["mongo"] == "connected"
            assert second.get("/api/auth/me", headers=supa).json()["id"] == user["id"]
            saved_business = second.get("/api/businesses", headers=supa).json()
            assert len(saved_business) == 1
            assert saved_business[0]["id"] == bid
            assert saved_business[0]["owner_user_id"] == user["id"]
            assert saved_business[0]["company_name"] == "Restart evidence"
            saved = second.get(f"/api/businesses/{bid}/tasks", headers=supa).json()
            assert (
                saved[0]["id"] == task.json()["id"]
                and saved[0]["status"] == "pending_approval"
            )
            assert (
                control[database].users.find_one({"user_id": user["id"]})[
                    "encrypted_data_key"
                ]
                == original_key
            )
            assert (
                control[database].auth_identities.count_documents(
                    {"subject": subject, "user_id": user["id"]}
                )
                == 1
            )
            # A persisted native session is still revoked correctly after restart.
            assert second.get("/api/auth/me", headers=native).status_code == 200
            assert (
                second.post(
                    "/api/auth/logout",
                    headers={**native, "X-Requested-With": "XMLHttpRequest"},
                ).status_code
                == 204
            )
            assert second.get("/api/auth/me", headers=native).status_code == 401
    finally:
        control.drop_database(database)
        control.close()
