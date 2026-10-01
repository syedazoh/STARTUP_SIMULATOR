"""Simulation control routes (business-scoped)"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from ..deps import get_owned_business
from ...database.utils import find_one
from ...models.business_schemas import BusinessOut
from ...models.schemas import SimulationStatusOut
from ...services.persistence import record_decision, snapshot_agents
from ...simulation import SimulationConfig, SimulationEngine

router = APIRouter(prefix="/api/businesses/{business_id}/simulation", tags=["simulation"])

MIN_SIMULATION_INTERVAL = 0.1
MAX_SIMULATION_TICKS = 1000
DEFAULT_SIMULATION_TICKS = 500
MAX_SIMULATION_DURATION = 3600.0
MAX_CONCURRENT_SIMULATIONS = 10


@router.post("/start")
async def start_simulation(
    payload: SimulationConfig, request: Request, business: BusinessOut = Depends(get_owned_business)
):
    if payload.min_interval < MIN_SIMULATION_INTERVAL:
        raise HTTPException(
            status_code=400,
            detail=f"min_interval must be at least {MIN_SIMULATION_INTERVAL} seconds.",
        )
    if payload.max_interval < payload.min_interval:
        raise HTTPException(
            status_code=400,
            detail="max_interval cannot be less than min_interval.",
        )

    # Enforce finite work budget even for unbounded requests
    if payload.ticks is None and payload.duration_seconds is None:
        payload.ticks = DEFAULT_SIMULATION_TICKS
    elif payload.ticks is not None and payload.ticks > MAX_SIMULATION_TICKS:
        payload.ticks = MAX_SIMULATION_TICKS
    if payload.duration_seconds is not None and payload.duration_seconds > MAX_SIMULATION_DURATION:
        payload.duration_seconds = MAX_SIMULATION_DURATION

    registry = request.app.state.agent_registry
    runtime = await registry.get_or_create(business)

    if runtime.simulation_engine is not None and runtime.simulation_engine.is_running:
        raise HTTPException(status_code=409, detail="Simulation already running")

    db = request.app.state.db
    running_count = await db["simulation_runs"].count_documents({"status": "running"})
    if running_count >= MAX_CONCURRENT_SIMULATIONS:
        raise HTTPException(
            status_code=429,
            detail="Maximum concurrent simulations limit reached.",
        )

    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)

    await db["simulation_runs"].insert_one({
        "business_id": business.id,
        "run_id": run_id,
        "started_at": started_at,
        "ended_at": None,
        "status": "running",
        "tick_count": 0,
        "config": payload.model_dump(),
    })

    async def on_decision(record):
        await record_decision(
            db,
            business.id,
            record["event_type"],
            record["data"],
            source="simulation",
            run_id=run_id,
            tick=record["tick"],
        )
        await db["simulation_runs"].update_one(
            {"business_id": business.id, "run_id": run_id}, {"$set": {"tick_count": record["tick"]}}
        )
        await snapshot_agents(db, business.id, runtime.agent_manager, run_id=run_id)

    async def on_complete(summary):
        now = datetime.now(timezone.utc)
        await db["run_summaries"].insert_one({
            "business_id": business.id,
            "run_id": run_id,
            "headline": summary.headline,
            "key_decisions": summary.key_decisions,
            "risks": summary.risks,
            "recommendation": summary.recommendation,
            "created_at": now,
        })
        # Marks the run "completed" whenever run() ends for any reason (tick limit
        # reached, or stop() cancelling it); stop_simulation() below overwrites this
        # with "stopped" for the user-initiated case, so the final status still
        # distinguishes "ran to completion" from "stopped early".
        await db["simulation_runs"].update_one(
            {"business_id": business.id, "run_id": run_id},
            {"$set": {"status": "completed", "ended_at": now}},
        )

    engine = SimulationEngine(runtime.agent_manager, on_decision=on_decision, on_complete=on_complete)
    runtime.simulation_engine = engine
    runtime.current_run_id = run_id
    engine.start(config=payload)

    return {"status": "started", "run_id": run_id}


@router.post("/stop")
async def stop_simulation(request: Request, business: BusinessOut = Depends(get_owned_business)):
    runtime = await request.app.state.agent_registry.get_or_create(business)
    engine: Optional[SimulationEngine] = runtime.simulation_engine
    if engine is None or not engine.is_running:
        raise HTTPException(status_code=409, detail="No simulation is running")

    await engine.stop()

    db = request.app.state.db
    await db["simulation_runs"].update_one(
        {"business_id": business.id, "run_id": runtime.current_run_id},
        {"$set": {"status": "stopped", "ended_at": datetime.now(timezone.utc)}},
    )
    return {"status": "stopped", "run_id": runtime.current_run_id}


@router.post("/pause")
async def pause_simulation(request: Request, business: BusinessOut = Depends(get_owned_business)):
    runtime = await request.app.state.agent_registry.get_or_create(business)
    engine: Optional[SimulationEngine] = runtime.simulation_engine
    if engine is None or not engine.is_running:
        raise HTTPException(status_code=409, detail="No simulation is running")
    engine.pause()
    return {"status": "paused"}


@router.post("/resume")
async def resume_simulation(request: Request, business: BusinessOut = Depends(get_owned_business)):
    runtime = await request.app.state.agent_registry.get_or_create(business)
    engine: Optional[SimulationEngine] = runtime.simulation_engine
    if engine is None or not engine.is_running:
        raise HTTPException(status_code=409, detail="No simulation is running")
    engine.resume()
    return {"status": "resumed"}


@router.get("/status", response_model=SimulationStatusOut)
async def simulation_status(request: Request, business: BusinessOut = Depends(get_owned_business)):
    runtime = await request.app.state.agent_registry.get_or_create(business)
    engine: Optional[SimulationEngine] = runtime.simulation_engine
    if engine is None:
        return SimulationStatusOut(is_running=False, tick_count=0, decision_log_size=0, run_id=None)
    status = engine.status()
    return SimulationStatusOut(**status, run_id=runtime.current_run_id)


@router.get("/runs/{run_id}/log")
async def get_run_log(
    run_id: str, request: Request, business: BusinessOut = Depends(get_owned_business), limit: int = 500
):
    db = request.app.state.db
    cursor = (
        db["decision_logs"]
        .find({"business_id": business.id, "simulation_run_id": run_id})
        .sort("tick", 1)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs


@router.get("/runs/{run_id}/summary")
async def get_run_summary(
    run_id: str, request: Request, business: BusinessOut = Depends(get_owned_business)
):
    db = request.app.state.db
    doc = await find_one(db["run_summaries"], {"business_id": business.id, "run_id": run_id})
    if doc is None:
        raise HTTPException(status_code=404, detail="Summary not available yet")
    doc["_id"] = str(doc["_id"])
    return doc


@router.get("/decision-log")
async def get_decision_log(
    request: Request,
    business: BusinessOut = Depends(get_owned_business),
    limit: int = 500,
    run_id: Optional[str] = None,
):
    """Get decision log entries for a business, optionally filtered by run_id."""
    db = request.app.state.db
    query = {"business_id": business.id}
    if run_id:
        query["simulation_run_id"] = run_id
    cursor = db["decision_logs"].find(query).sort("tick", 1).limit(limit)
    docs = await cursor.to_list(length=limit)
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs


@router.get("/simulation-runs")
async def get_simulation_runs(request: Request, business: BusinessOut = Depends(get_owned_business)):
    """Get all simulation runs for a business."""
    db = request.app.state.db
    cursor = db["simulation_runs"].find({"business_id": business.id}).sort("started_at", -1)
    docs = await cursor.to_list(length=100)
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs
