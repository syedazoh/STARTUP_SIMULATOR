import asyncio
import time
import pytest
from fastapi import HTTPException
from mongomock_motor import AsyncMongoMockClient
from app.services import jobs


@pytest.mark.asyncio
async def test_idempotency_isolation_and_body_conflict():
    db = AsyncMongoMockClient().db
    a = await jobs.enqueue(db, "a", "owner", "daily_brief", {}, "same")
    assert (
        a["job_id"]
        == (await jobs.enqueue(db, "a", "owner", "daily_brief", {}, "same"))["job_id"]
    )
    assert (
        a["job_id"]
        != (await jobs.enqueue(db, "b", "other", "daily_brief", {}, "same"))["job_id"]
    )
    with pytest.raises(HTTPException):
        await jobs.enqueue(db, "a", "owner", "daily_brief", {"different": True}, "same")


@pytest.mark.asyncio
async def test_atomic_claim_and_expired_lease_recovery():
    db = AsyncMongoMockClient().db
    await jobs.enqueue(db, "a", "owner", "daily_brief", {}, "same", clock=100)
    rows = await asyncio.gather(jobs.claim(db, 101), jobs.claim(db, 101))
    assert sum(r is not None for r in rows) == 1
    original = next(r for r in rows if r)
    recovered = await jobs.claim(db, 282)
    assert (
        recovered["job_id"] == original["job_id"]
        and recovered["lease_token"] != original["lease_token"]
        and recovered["attempts"] == 2
    )


@pytest.mark.asyncio
async def test_retry_budget_and_scrubbed_error(monkeypatch):
    db = AsyncMongoMockClient().db
    await jobs.enqueue(db, "a", "owner", "daily_brief", {}, "same")

    async def fail(*a):
        raise RuntimeError("private provider credential")

    monkeypatch.setattr(jobs, "handle", fail)
    for _ in range(3):
        result = await jobs.run_once(db, None, clock=time.time() + 1000)
    assert result["status"] == "failed" and result["attempts"] == 3
    assert "credential" not in result["error"]


@pytest.mark.asyncio
async def test_redis_outage_retains_durable_job(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "redis_url", "redis://127.0.0.1:1")
    db = AsyncMongoMockClient().db
    job = await jobs.enqueue(db, "a", "owner", "daily_brief", {}, "same")
    assert (await jobs.claim(db))["job_id"] == job["job_id"]


@pytest.mark.asyncio
async def test_old_lease_cannot_commit_over_reclaimed_job(monkeypatch):
    db = AsyncMongoMockClient().db
    job = await jobs.enqueue(db, "a", "owner", "daily_brief", {}, "same")

    async def replace(db, registry, row):
        await db["background_jobs"].update_one(
            {"_id": row["_id"]}, {"$set": {"lease_token": "replacement"}}
        )
        return {"ok": True}

    monkeypatch.setattr(jobs, "handle", replace)
    await jobs.run_once(db, None)
    assert (await db["background_jobs"].find_one({"_id": job["job_id"]}))[
        "status"
    ] == "running"
