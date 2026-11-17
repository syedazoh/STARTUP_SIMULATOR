"""Real Mongo reconnect and expired-lease recovery. Never uses the configured production DB."""

import asyncio
import os
import time
from uuid import uuid4
import pytest
from pymongo import MongoClient
from fastapi.testclient import TestClient
from app.config import settings
from app.main import app
from app.services import jobs


def test_jobs_and_index_recover_across_actual_mongo_reconnect(monkeypatch):
    uri = os.environ.get("MONGODB_INTEGRATION_URL")
    if not uri:
        pytest.skip("MONGODB_INTEGRATION_URL required for real restart evidence")
    name = "automation_test_" + uuid4().hex
    control = MongoClient(uri, serverSelectionTimeoutMS=5000)
    control.admin.command("ping")
    monkeypatch.setattr(settings, "mongodb_url", uri)
    monkeypatch.setattr(settings, "mongodb_db_name", name)
    monkeypatch.setattr(settings, "background_jobs_enabled", True)
    monkeypatch.setattr(settings, "rag_dense_enabled", False)
    monkeypatch.setattr(settings, "rag_reranker_enabled", False)
    original = jobs.worker_loop

    async def idle(app):
        await asyncio.Event().wait()

    monkeypatch.setattr(jobs, "worker_loop", idle)
    try:
        with TestClient(app) as first:
            assert (
                first.post(
                    "/api/auth/register",
                    json={
                        "email": "automation-restart@example.com",
                        "password": "test-only-password",
                    },
                ).status_code
                == 201
            )
            login = first.post(
                "/api/auth/login",
                json={
                    "email": "automation-restart@example.com",
                    "password": "test-only-password",
                },
            ).json()
            h = {"Authorization": "Bearer " + login["access_token"]}
            bid = first.post(
                "/api/businesses",
                headers=h,
                json={"company_name": "Restart acceptance", "industry": "Software"},
            ).json()["id"]
            root = f"/api/businesses/{bid}"
            brief = first.post(
                root + "/jobs",
                headers=h,
                json={"kind": "daily_brief", "idempotency_key": "restart"},
            ).json()
            doc = first.post(
                root + "/knowledge",
                headers=h,
                json={
                    "key": "policy",
                    "title": "Policy",
                    "text": "Campaign approval requires owner review.",
                    "departments": ["finance"],
                },
            )
            assert doc.status_code == 202, doc.text
            control[name].background_jobs.update_one(
                {"job_id": brief["job_id"]},
                {
                    "$set": {
                        "status": "running",
                        "lease_token": "dead-process",
                        "lease_until": time.time() - 1,
                        "attempts": 1,
                    }
                },
            )
        monkeypatch.setattr(jobs, "worker_loop", original)
        with TestClient(app) as second:
            until = time.monotonic() + 15
            while time.monotonic() < until:
                state = second.get(root + "/automation", headers=h).json()
                if all(j["status"] == "succeeded" for j in state["jobs"]):
                    break
                time.sleep(0.1)
            assert len(state["jobs"]) == 2 and all(
                j["status"] == "succeeded" for j in state["jobs"]
            ), state
            assert (
                next(j for j in state["jobs"] if j["job_id"] == brief["job_id"])[
                    "attempts"
                ]
                == 2
            )
            assert state["documents"][0]["status"] == "ready"
            assert second.post(
                root + "/knowledge/search",
                headers=h,
                json={"query": "campaign approval", "department": "finance"},
            ).json()["results"]
            assert (
                control[name].business_briefs.count_documents({"business_id": bid}) == 1
            )
    finally:
        control.drop_database(name)
        control.close()
