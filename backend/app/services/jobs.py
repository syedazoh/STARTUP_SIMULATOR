"""Mongo is the durable queue; optional Redis hints only reduce polling latency.
One API process owns the existing in-memory agent registry. No live effects here.
"""

import asyncio
import hashlib
import json
import time
from uuid import uuid4
from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from ..config import settings
from ..database.mongodb import InMemoryDatabase

SAFE_ACTIONS = {
    "budget_request",
    "campaign_launch",
    "recruitment_request",
    "resource_request",
    "dataset_launch",
}


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), default=str, allow_nan=False
        ).encode()
    ).hexdigest()


def persistent(db):
    if isinstance(db, InMemoryDatabase):
        raise HTTPException(
            503, "Durable MongoDB is required; in-memory storage is not a queue"
        )


def public(doc):
    return {k: v for k, v in doc.items() if k not in {"_id", "lease_token"}}


async def wake():
    if not settings.redis_url:
        return
    try:
        from redis.asyncio import Redis

        async with Redis.from_url(
            settings.redis_url, socket_connect_timeout=1, socket_timeout=1
        ) as redis:
            await redis.lpush("startup:job-wakeup", "1")
            await redis.ltrim("startup:job-wakeup", 0, 99)
    except Exception:
        pass  # Mongo polling remains authoritative.


async def enqueue(db, business_id, actor, kind, payload, key, *, clock=None):
    persistent(db)
    job_id = digest([business_id, kind, key])
    now = time.time() if clock is None else clock
    doc = {
        "_id": job_id,
        "job_id": job_id,
        "business_id": business_id,
        "requested_by": actor,
        "kind": kind,
        "payload": payload,
        "request_digest": digest(payload),
        "status": "queued",
        "attempts": 0,
        "max_attempts": 3,
        "run_after": now,
        "created_ts": now,
        "updated_ts": now,
        "lease_until": 0,
        "result": None,
        "error": None,
    }
    try:
        await db["background_jobs"].insert_one(doc)
    except DuplicateKeyError:
        doc = await db["background_jobs"].find_one({"_id": job_id})
        if not doc or doc["request_digest"] != digest(payload):
            raise HTTPException(
                409, "Idempotency key already used with different input"
            )
    await wake()
    return public(doc)


async def claim(db, clock=None):
    now = time.time() if clock is None else clock
    return await db["background_jobs"].find_one_and_update(
        {
            "$or": [
                {
                    "status": {"$in": ["queued", "retry_scheduled"]},
                    "run_after": {"$lte": now},
                },
                {"status": "running", "lease_until": {"$lte": now}},
            ]
        },
        {
            "$set": {
                "status": "running",
                "lease_token": str(uuid4()),
                "lease_until": now + 180,
                "updated_ts": now,
            },
            "$inc": {"attempts": 1},
        },
        sort=[("run_after", 1)],
        return_document=ReturnDocument.AFTER,
    )


async def reconcile(db):
    # Approval and outbox marker are one task write; queue insertion is repairable.
    tasks = (
        await db["tasks"]
        .find(
            {
                "status": "approved",
                "deferred_execution": True,
                "deferred_enqueued": {"$ne": True},
            }
        )
        .to_list(length=100)
    )
    for t in tasks:
        await enqueue(
            db,
            t["business_id"],
            t["approved_by"],
            "execute_task",
            {"task_id": t["task_id"]},
            t["task_id"],
        )
        await db["tasks"].update_one(
            {
                "task_id": t["task_id"],
                "business_id": t["business_id"],
                "status": "approved",
            },
            {"$set": {"deferred_enqueued": True}},
        )


class Uncertain(Exception):
    pass


async def handle(db, registry, job):
    from ..api.routes.businesses import _to_business_out

    doc = await db["businesses"].find_one({"business_id": job["business_id"]})
    if not doc or doc["owner_user_id"] != job["requested_by"]:
        raise HTTPException(403, "Workspace ownership changed")
    business = _to_business_out(doc)
    p = job["payload"]
    kind = job["kind"]
    if p.get("_mcp_grant"):
        grant = await db["mcp_grants"].find_one(
            {
                "_id": p["_mcp_grant"],
                "business_id": business.id,
                "user_id": job["requested_by"],
                "revoked": False,
                "expires_ts": {"$gt": time.time()},
            }
        )
        if (
            not grant
            or "tasks:propose" not in grant["scopes"]
            or p["department"] not in grant["departments"]
        ):
            raise HTTPException(403, "MCP capability expired or revoked")
    if kind == "ceo_plan":
        from .supervision import propose_plan

        plan = await propose_plan(
            db, registry, business, p["goal"], plan_id=job["job_id"]
        )
        return {"plan_id": plan["plan_id"], "status": plan["status"]}
    if kind == "propose_task":
        from .tasks import create_task

        task = await create_task(
            db,
            registry,
            business,
            p["department"],
            p["action_type"],
            p["payload"],
            source="mcp",
            task_id=job["job_id"],
            force_owner_review=True,
        )
        return {"task_id": task["task_id"], "status": task["status"]}
    if kind == "index_document":
        from .knowledge import index_document

        return await index_document(db, business.id, p["document_id"], p["version"])
    if kind == "daily_brief":
        rows = (
            await db["tasks"]
            .find({"business_id": business.id})
            .sort("created_at", -1)
            .to_list(length=200)
        )
        counts = {}
        for t in rows:
            counts[t["status"]] = counts.get(t["status"], 0) + 1
        brief = {
            "_id": job["job_id"],
            "business_id": business.id,
            "brief_id": job["job_id"],
            "status_counts": counts,
            "task_ids": [t["task_id"] for t in rows],
            "sample_limit": 200,
            "created_ts": time.time(),
            "summary": "Saved task status counts; execution is not proof of real-world business success.",
        }
        await db["business_briefs"].update_one(
            {"_id": job["job_id"]}, {"$setOnInsert": brief}, upsert=True
        )
        saved = await db["business_briefs"].find_one({"_id": job["job_id"]})
        return public(saved)
    if kind == "execute_task":
        from .tasks import execute_task

        task = await db["tasks"].find_one(
            {"business_id": business.id, "task_id": p["task_id"]}
        )
        if not task or task["action_type"] not in SAFE_ACTIONS:
            raise HTTPException(
                409, "Only approved internal simulation work can run here"
            )
        if task["status"] == "executed":
            return {"task_id": task["task_id"], "status": "executed", "replayed": True}
        if task["status"] in {"executing", "reconciliation_required"}:
            await db["tasks"].update_one(
                {
                    "business_id": business.id,
                    "task_id": task["task_id"],
                    "status": "executing",
                },
                {"$set": {"status": "reconciliation_required"}},
            )
            raise Uncertain(
                "Interrupted execution; review saved evidence before any replay"
            )
        if task["status"] != "approved" or not task.get("ceo_authorized"):
            raise HTTPException(409, "Task is no longer approved")
        done = await execute_task(db, registry, business, task)
        return {"task_id": done["task_id"], "status": done["status"]}
    raise HTTPException(422, "Unknown job kind")


async def run_once(db, registry, clock=None):
    job = await claim(db, clock)
    if not job:
        return None
    lease = {"_id": job["_id"], "status": "running", "lease_token": job["lease_token"]}
    try:
        if job["attempts"] > job["max_attempts"]:
            raise HTTPException(409, "Retry budget exhausted")
        result = await asyncio.wait_for(handle(db, registry, job), timeout=120)
        update = {"status": "succeeded", "result": result, "error": None}
    except asyncio.CancelledError:
        raise
    except Uncertain as exc:
        update = {"status": "reconciliation_required", "error": str(exc)}
    except Exception as exc:
        task = (
            await db["tasks"].find_one(
                {
                    "business_id": job["business_id"],
                    "task_id": job["payload"].get("task_id"),
                }
            )
            if job["kind"] == "execute_task"
            else None
        )
        if task and task["status"] == "executing":
            await db["tasks"].update_one(
                {
                    "business_id": job["business_id"],
                    "task_id": task["task_id"],
                    "status": "executing",
                },
                {"$set": {"status": "reconciliation_required"}},
            )
            update = {
                "status": "reconciliation_required",
                "error": "Execution outcome uncertain; inspect evidence before replay",
            }
        else:
            retry = (
                not (isinstance(exc, HTTPException) and exc.status_code < 500)
                and job["attempts"] < job["max_attempts"]
            )
            update = {
                "status": "retry_scheduled" if retry else "failed",
                "run_after": time.time() + min(60, 2 ** job["attempts"]),
                "error": (
                    str(exc.detail)
                    if isinstance(exc, HTTPException)
                    else "Job failed or timed out; inspect saved evidence"
                ),
            }
    update.update(updated_ts=time.time(), lease_until=0)
    await db["background_jobs"].update_one(lease, {"$set": update})
    return public({**job, **update})


async def worker_loop(app):
    persistent(app.state.db)
    while True:
        try:
            from .knowledge import recover_index_jobs
            from .deadlines import scan_deadlines

            await recover_index_jobs(app.state.db)
            await reconcile(app.state.db)
            await scan_deadlines(app.state.db)
            worked = await run_once(app.state.db, app.state.agent_registry)
            app.state.worker_heartbeat = time.time()
            app.state.worker_error = None
            if worked:
                continue
        except asyncio.CancelledError:
            raise
        except Exception:
            app.state.worker_error = (
                "Worker storage unavailable; queued records are retained"
            )
        if settings.redis_url:
            try:
                from redis.asyncio import Redis

                async with Redis.from_url(
                    settings.redis_url, socket_connect_timeout=1, socket_timeout=2
                ) as redis:
                    await redis.blpop("startup:job-wakeup", timeout=1)
                continue
            except Exception:
                pass
        await asyncio.sleep(1)
