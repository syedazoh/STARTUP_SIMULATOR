"""Synthetic snapshot import and scoped access; no provider or agent side effects."""

import csv
import hashlib
import io
import json
import re
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from pydantic import ValidationError
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from ..database.utils import find_one
from ..models.demo_dataset import Dataset, TABLES
from .audit import record_audit

MAX_BYTES = 1024 * 1024
DEPARTMENTS = {"finance", "marketing", "hr", "operations", "ceo"}
ROLE_TABLES = {
    "finance": ("company", "sales", "expenses", "campaigns", "inventory", "orders"),
    "marketing": ("goals", "campaigns", "inventory"),
    "hr": ("company", "goals", "candidates"),
    "operations": ("company", "inventory", "orders", "campaigns"),
    "ceo": (
        "company",
        "goals",
        "sales",
        "expenses",
        "campaigns",
        "inventory",
        "orders",
    ),
}


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def parse_upload(content: bytes, format: str) -> Dataset:
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "Dataset exceeds 1 MiB")
    row = None
    try:
        text = content.decode("utf-8-sig")
        if format == "json":
            value = json.loads(text)
        elif format == "csv":
            reader = csv.DictReader(io.StringIO(text))
            if reader.fieldnames != ["record_type", "record_json"]:
                raise ValueError("CSV requires record_type,record_json columns")
            value = {name: [] for name in TABLES}
            metadata = False
            for row, cells in enumerate(reader, 2):
                if None in cells or None in cells.values():
                    raise ValueError("CSV column count mismatch")
                kind = cells["record_type"]
                record = json.loads(cells["record_json"])
                if not isinstance(record, dict):
                    raise ValueError("record_json must be an object")
                if kind == "metadata" and not metadata:
                    if any(k in record for k in TABLES):
                        raise ValueError("Metadata cannot contain tables")
                    value.update(record)
                    metadata = True
                elif kind in TABLES:
                    value[kind].append(record)
                else:
                    raise ValueError("Unknown record_type or repeated metadata")
            if not metadata:
                raise ValueError("Exactly one metadata row required")
        else:
            raise ValueError("Supported formats: json, csv")
        return Dataset.model_validate(value)
    except ValidationError as exc:
        errors = []
        for e in exc.errors(include_input=False, include_context=False):
            loc = e["loc"]
            # CSV validation paths identify table/record index; recover physical row.
            physical = None
            if format == "csv" and len(loc) > 1 and isinstance(loc[1], int):
                matching = [
                    i
                    for i, cells in enumerate(csv.DictReader(io.StringIO(text)), 2)
                    if cells["record_type"] == loc[0]
                ]
                if loc[1] < len(matching):
                    physical = matching[loc[1]]
            errors.append(
                {
                    "row": physical,
                    "field": ".".join(map(str, loc)) or "relationships",
                    "message": e["msg"],
                }
            )
        raise HTTPException(422, errors) from exc
    except (ValueError, UnicodeError, csv.Error, RecursionError) as exc:
        raise HTTPException(
            422,
            [
                {
                    "row": row,
                    "field": "record_json" if format == "csv" else "file",
                    "message": str(exc)[:300],
                }
            ],
        ) from exc


def storage_id(business_id, dataset_id):
    return digest([business_id, dataset_id])


async def preview(db, business_id, data):
    body = data.model_dump(mode="json")
    old = await find_one(
        db["demo_datasets"],
        {"_id": storage_id(business_id, data.dataset_id), "business_id": business_id},
    )
    checksum = digest(body)
    return {
        "digest": checksum,
        "dataset_id": data.dataset_id,
        "synthetic": True,
        "counts": {name: len(body[name]) for name in TABLES},
        "preview": body,
        "duplicate": bool(old and old["digest"] == checksum),
        "conflict": bool(old and old["digest"] != checksum),
    }


async def commit_import(db, business_id, data, expected_digest):
    result = await preview(db, business_id, data)
    if result["digest"] != expected_digest:
        raise HTTPException(409, "Content changed since preview; preview again")
    doc = {
        "_id": storage_id(business_id, data.dataset_id),
        "business_id": business_id,
        "import_id": str(uuid4()),
        "digest": result["digest"],
        "synthetic": True,
        "active": True,
        "data": data.model_dump(mode="json"),
        "created_at": datetime.now(timezone.utc),
    }
    try:
        # One bounded document: Mongo's unique _id makes concurrent imports atomic.
        await db["demo_datasets"].insert_one(doc)
    except DuplicateKeyError:
        old = await find_one(
            db["demo_datasets"], {"_id": doc["_id"], "business_id": business_id}
        )
        if old is None or old["digest"] != doc["digest"]:
            raise HTTPException(
                409, "Dataset ID already has different content; use a new dataset ID"
            )
        if not old["active"]:
            # Reset keeps a tombstone; explicit reimport starts a fresh run generation.
            doc = await db["demo_datasets"].find_one_and_update(
                {"_id": old["_id"], "business_id": business_id, "active": False},
                {
                    "$set": {
                        "active": True,
                        "import_id": doc["import_id"],
                        "created_at": doc["created_at"],
                    }
                },
                return_document=ReturnDocument.AFTER,
            )
            if doc is None:
                raise HTTPException(409, "Concurrent reimport; reload")
        else:
            return {"import_id": old["import_id"], "duplicate": True}
    return {"import_id": doc["import_id"], "duplicate": False}


async def load_dataset(db, business_id, import_id):
    doc = await find_one(
        db["demo_datasets"],
        {"business_id": business_id, "import_id": import_id, "active": True},
    )
    if doc is None:
        raise HTTPException(404, "Active demo import not found")
    return doc


async def department_records(db, business_id, import_id, department):
    if department not in DEPARTMENTS:
        raise HTTPException(422, "Unknown department")
    doc = await load_dataset(db, business_id, import_id)
    return {
        "import_id": import_id,
        "dataset_digest": doc["digest"],
        "synthetic": True,
        "currency": doc["data"]["currency"],
        "as_of": doc["data"]["as_of"],
        "records": {name: doc["data"][name] for name in ROLE_TABLES[department]},
    }


async def retrieve_references(db, business_id, import_id, department, query):
    """Small-corpus lexical RAG; permission filtering precedes ranking. No calculations."""
    if department not in DEPARTMENTS:
        raise HTTPException(422, "Unknown department")
    doc = await load_dataset(db, business_id, import_id)
    terms = set(re.findall(r"\w+", query.lower()))
    ranked = []
    for ref in doc["data"]["references"]:
        if ref["department"] not in {"all", department}:
            continue
        score = len(
            terms & set(re.findall(r"\w+", (ref["title"] + " " + ref["text"]).lower()))
        )
        if score:
            ranked.append(
                {
                    "score": score,
                    "text": ref["text"],
                    "citation": {
                        "import_id": import_id,
                        "document_id": ref["id"],
                        "version": ref["version"],
                        "title": ref["title"],
                    },
                }
            )
    return sorted(ranked, key=lambda r: (-r["score"], r["citation"]["document_id"]))[:3]


async def reset_preview(db, business_id, import_id):
    doc = await load_dataset(db, business_id, import_id)
    tasks = (
        await db["tasks"]
        .find({"business_id": business_id, "demo_import_id": import_id})
        .to_list(length=None)
    )
    return {
        "import_id": import_id,
        "digest": doc["digest"],
        "synthetic": True,
        "records": sum(len(doc["data"][name]) for name in TABLES) + 1,
        "tasks": len(tasks),
        "task_ids": [t["task_id"] for t in tasks],
        "effect": "Archive this demo generation and cancel pending demo work. Keep approval/audit evidence; reimport to restart.",
    }


async def reset_demo(db, business, import_id, expected_digest):
    info = await reset_preview(db, business.id, import_id)
    if info["digest"] != expected_digest:
        raise HTTPException(409, "Reset preview changed")
    changed = await db["demo_datasets"].find_one_and_update(
        {
            "business_id": business.id,
            "import_id": import_id,
            "active": True,
            "digest": expected_digest,
        },
        {"$set": {"active": False}},
        return_document=ReturnDocument.AFTER,
    )
    if changed is None:
        raise HTTPException(409, "Demo already reset")
    tasks = (
        await db["tasks"]
        .find(
            {
                "business_id": business.id,
                "demo_import_id": import_id,
                "action_type": "dataset_launch",
            }
        )
        .to_list(length=None)
    )
    for task in tasks:
        changes = {"demo_archived": True}
        if task["status"] in {
            "pending_ceo_review",
            "pending_approval",
            "needs_changes",
            "approved",
            "blocked",
        }:
            changes.update(
                status="cancelled",
                owner_feedback="Synthetic demo reset; approval and review evidence retained.",
            )
        await db["tasks"].update_one(
            {
                "task_id": task["task_id"],
                "business_id": business.id,
                "demo_import_id": import_id,
                "status": task["status"],
            },
            {"$set": changes},
        )
    await record_audit(
        db, business.owner_user_id, business.id, "demo_reset", target_id=import_id
    )
    return info
