"""Versioned in-app deadlines. No external notification side effects."""

import time
from datetime import datetime, timezone
from fastapi import HTTPException
from pymongo import ReturnDocument
from .jobs import digest, persistent
from .audit import record_audit

CLOSED = {
    "executed",
    "verified_complete",
    "failed",
    "denied",
    "rejected",
    "cancelled",
    "expired",
    "reconciliation_required",
}
EDITABLE = {
    "pending_approval",
    "needs_changes",
    "pending_ceo_review",
    "needs_revision",
    "awaiting_asset",
}


async def set_deadline(db, business, task, actor, payload):
    persistent(db)
    now = time.time()
    due = payload.due_at.timestamp()
    if not now < due <= now + 366 * 86400:
        raise HTTPException(422, "Due date must be in the next 366 days")
    if task["status"] not in EDITABLE:
        raise HTTPException(409, "Only pending work can change its deadline")
    version = payload.expected_version
    match = {
        "business_id": business.id,
        "task_id": task["task_id"],
        "status": task["status"],
        "deadline_version": {"$in": [None, 0]} if version == 0 else version,
    }
    fields = {
        "due_at": payload.due_at.isoformat(),
        "due_ts": due,
        "deadline_version": version + 1,
        "deadline_reason": payload.reason.strip(),
        "reminder_minutes": payload.reminder_minutes,
        "escalation_minutes": payload.escalation_minutes,
        "deadline_flags": [],
        "deadline_active": True,
        "deadline_next_check": max(now, due - payload.reminder_minutes * 60),
    }
    changed = await db["tasks"].find_one_and_update(
        match, {"$set": fields}, return_document=ReturnDocument.AFTER
    )
    if not changed:
        raise HTTPException(409, "Task or deadline changed; refresh before editing")
    await record_audit(
        db,
        actor,
        business.id,
        "deadline_changed",
        target_id=task["task_id"],
        details={
            "version": version + 1,
            "due_at": fields["due_at"],
            "reason": fields["deadline_reason"],
        },
    )
    return changed


async def scan_deadlines(db, clock=None):
    now = time.time() if clock is None else clock
    tasks = (
        await db["tasks"]
        .find({"deadline_active": True, "deadline_next_check": {"$lte": now}})
        .sort("deadline_next_check", 1)
        .to_list(length=100)
    )
    for t in tasks:
        match = {
            "business_id": t["business_id"],
            "task_id": t["task_id"],
            "deadline_version": t["deadline_version"],
        }
        if t["status"] in CLOSED:
            await db["tasks"].update_one(match, {"$set": {"deadline_active": False}})
            continue
        business = await db["businesses"].find_one({"business_id": t["business_id"]})
        if not business:
            continue
        flags = set(t.get("deadline_flags", []))
        stages = [
            ("reminder", t["due_ts"] - t.get("reminder_minutes", 60) * 60),
            ("overdue", t["due_ts"]),
            ("escalation", t["due_ts"] + t.get("escalation_minutes", 60) * 60),
        ]
        for kind, at in stages:
            if at <= now and kind not in flags:
                key = digest(
                    [t["business_id"], t["task_id"], t["deadline_version"], kind]
                )
                await db["notifications"].update_one(
                    {"_id": key},
                    {
                        "$setOnInsert": {
                            "notification_id": key,
                            "business_id": t["business_id"],
                            "task_id": t["task_id"],
                            "deadline_version": t["deadline_version"],
                            "kind": kind,
                            "due_at": t["due_at"],
                            "created_ts": now,
                            "recipient_user_id": business["owner_user_id"],
                            "recipient": (
                                "ceo_and_owner" if kind == "escalation" else "owner"
                            ),
                            "read": False,
                        }
                    },
                    upsert=True,
                )
                flags.add(kind)
        future = [at for kind, at in stages if kind not in flags]
        await db["tasks"].update_one(
            match,
            {
                "$set": {
                    "deadline_flags": sorted(flags),
                    "deadline_active": bool(future),
                    "deadline_next_check": min(future) if future else now,
                }
            },
        )
    return len(tasks)


async def notifications(db, business_id):
    rows = (
        await db["notifications"]
        .find({"business_id": business_id})
        .sort("created_ts", -1)
        .to_list(length=200)
    )
    output = []
    for n in rows:
        task = await db["tasks"].find_one(
            {"business_id": business_id, "task_id": n["task_id"]}
        )
        if (
            task
            and task.get("deadline_version") == n["deadline_version"]
            and task["status"] not in CLOSED
        ):
            output.append({k: v for k, v in n.items() if k != "_id"})
    return output
