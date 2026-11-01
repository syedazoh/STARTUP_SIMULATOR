"""Regressions for the reviewed task and simulation failure boundaries."""

import asyncio
import io
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from mongomock_motor import AsyncMongoMockClient
from PIL import Image
from pydantic import ValidationError

from app.services import media_assets
from app.simulation.config import SimulationConfig
from app.database.utils import ensure_unique_index
from app.services.run_summary import summarize_tasks
from app.simulation.simulation_engine import SimulationEngine
from tests.test_execution_supervision import client, account, business


def image_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), "blue").save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_stale_upload_does_not_reopen_terminal_task(tmp_path, monkeypatch):
    monkeypatch.setattr(media_assets, "UPLOAD_DIR", tmp_path)
    db = AsyncMongoMockClient().test
    stale = {
        "task_id": "one",
        "business_id": "biz",
        "status": "awaiting_asset",
        "ceo_authorized": True,
        "asset_id": None,
    }
    await db.tasks.insert_one({**stale, "status": "executed"})
    with pytest.raises(HTTPException) as error:
        await media_assets.upload_asset(
            db, "biz", stale, "a.png", image_bytes(), "image", "image/png"
        )
    assert error.value.status_code == 409
    assert (await db.tasks.find_one({"task_id": "one"}))["status"] == "executed"
    assert await db.media_assets.count_documents({}) == 0
    assert list(tmp_path.rglob("*.png")) == []


@pytest.mark.asyncio
async def test_competing_uploads_attach_exactly_one_asset(tmp_path, monkeypatch):
    monkeypatch.setattr(media_assets, "UPLOAD_DIR", tmp_path)
    db = AsyncMongoMockClient().test
    task = {
        "task_id": "one",
        "business_id": "biz",
        "status": "awaiting_asset",
        "ceo_authorized": True,
        "asset_id": None,
    }
    await db.tasks.insert_one(task.copy())
    results = await asyncio.gather(
        *(
            media_assets.upload_asset(
                db, "biz", task, "a.png", image_bytes(), "image", "image/png"
            )
            for _ in range(2)
        ),
        return_exceptions=True,
    )
    assert (
        sum(isinstance(r, HTTPException) and r.status_code == 409 for r in results) == 1
    )
    assert await db.media_assets.count_documents({}) == 1
    saved = await db.tasks.find_one({"task_id": "one"})
    asset = await db.media_assets.find_one({"asset_id": saved["asset_id"]})
    assert saved["asset_sha256"] == asset["sha256"]
    assert len(list(tmp_path.rglob("*.png"))) == 1


@pytest.mark.parametrize(
    "content,name,kind,mime",
    [
        (b"not an image", "a.png", "image", "image/png"),
        (b"", "a.png", "image", "image/png"),
        (image_bytes(), "a.jpg", "image", "image/jpeg"),
        (image_bytes(), "a.png", "video", "video/mp4"),
    ],
)
@pytest.mark.asyncio
async def test_invalid_media_has_no_file_or_database_effect(
    tmp_path, monkeypatch, content, name, kind, mime
):
    monkeypatch.setattr(media_assets, "UPLOAD_DIR", tmp_path)
    db = AsyncMongoMockClient().test
    with pytest.raises(HTTPException) as error:
        await media_assets.upload_asset(
            db, "biz", {"task_id": "one"}, name, content, kind, mime
        )
    assert error.value.status_code == 422
    assert await db.media_assets.count_documents({}) == 0
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "values",
    [
        {"ticks": 0},
        {"ticks": -1},
        {"duration_seconds": 0},
    {"max_interval": 61},
        {"min_interval": 2, "max_interval": 1},
        {"event_weights": {"unknown": 1}},
        {"event_weights": {"budget_request": -1}},
        {
            "event_weights": {
                k: 0
                for k in (
                    "budget_request",
                    "campaign_launch",
                    "recruitment_request",
                    "resource_request",
                )
            }
        },
        {"event_weights": {"budget_request": float("inf")}},
        {"event_weights": {"budget_request": 1e308, "campaign_launch": 1e308}},
    ],
)
def test_bad_simulation_config_rejected(values):
    with pytest.raises(ValidationError):
        SimulationConfig(**values)


@pytest.mark.asyncio
async def test_required_index_failure_is_not_suppressed():
    async def deny(*args, **kwargs):
        raise PermissionError("fixture index permission denied")

    with pytest.raises(PermissionError):
        await ensure_unique_index(SimpleNamespace(create_index=deny), "email")


@pytest.mark.asyncio
async def test_queued_only_run_does_not_claim_execution_or_expenses():
    db = AsyncMongoMockClient().test
    await db.tasks.insert_many(
        [
            {
                "task_id": str(i),
                "business_id": "biz",
                "run_id": "run",
                "status": "pending_approval",
                "action_type": "campaign_launch",
            }
            for i in range(10)
        ]
    )
    summary = await summarize_tasks(db, "biz", "run")
    assert "0 executed, 10 pending" in summary.headline
    assert any("$0.00" in line for line in summary.key_decisions)
    assert summary.risks


@pytest.mark.asyncio
async def test_tick_failure_finishes_as_failed():
    outcomes = []

    async def fail(*args):
        raise RuntimeError("fixture failure")

    async def finish(status, summary, error):
        outcomes.append((status, error))

    manager = SimpleNamespace(agents={})
    engine = SimulationEngine(manager, on_finish=finish)
    engine._tick = fail
    with pytest.raises(RuntimeError):
        await engine.run(SimulationConfig(ticks=1, min_interval=0.1, max_interval=0.1))
    assert outcomes == [("failed", "simulation_tick_failed")]


def test_concurrent_http_starts_accept_only_one(client):
    from concurrent.futures import ThreadPoolExecutor

    owner = account(client)
    bid = business(client, owner)

    def start():
        return client.post(
            f"/api/businesses/{bid}/simulation/start",
            headers=owner,
            json={"ticks": 20, "min_interval": 1, "max_interval": 1},
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        codes = list(pool.map(lambda _: start(), range(2)))
    assert sorted(codes) == [200, 409]


def test_actionable_queue_keeps_old_pending_task(client):
    from app.main import app
    from tests.test_execution_supervision import pending
    from datetime import datetime, timezone, timedelta

    owner = account(client)
    bid = business(client, owner)
    tid = pending(client, owner, bid)

    async def insert_completed():
        original = await app.state.db.tasks.find_one({"task_id": tid})
        await app.state.db.tasks.insert_many(
            [
                {
                    **original,
                    "_id": f"completed-{i}",
                    "task_id": f"completed-{i}",
                    "status": "executed",
                    "created_at": datetime.now(timezone.utc) + timedelta(seconds=i),
                }
                for i in range(201)
            ]
        )

    client.portal.call(insert_completed)
    rows = client.get(
        f"/api/businesses/{bid}/tasks?actionable=true", headers=owner
    ).json()
    assert [row["id"] for row in rows] == [tid]
