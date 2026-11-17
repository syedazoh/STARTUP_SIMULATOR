"""Owner-scoped jobs, knowledge, deadlines and private MCP credentials."""

import time
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from ..deps import get_current_user, get_owned_business, get_owned_task
from ...models.automation_schemas import (
    JobIn,
    DeadlineIn,
    DocumentIn,
    SearchIn,
    MCPGrantIn,
)
from ...models.task_schemas import to_task_out
from ...core.rate_limit import RateLimiter, rate_limit_dependency
from ...config import settings
from ...database.mongodb import InMemoryDatabase
from ...services import jobs, deadlines, knowledge

_limited = Depends(
    rate_limit_dependency(RateLimiter(max_requests=90, window_seconds=60))
)
router = APIRouter(
    prefix="/api/businesses/{business_id}",
    tags=["automation and knowledge"],
    dependencies=[_limited],
)
task_router = APIRouter(
    prefix="/api/tasks", tags=["deadlines"], dependencies=[_limited]
)


def enabled():
    if not settings.background_jobs_enabled:
        raise HTTPException(
            503, "Set BACKGROUND_JOBS_ENABLED=True and restart the backend"
        )


@router.get("/automation")
async def overview(request: Request, business=Depends(get_owned_business)):
    db = request.app.state.db
    match = {"business_id": business.id}
    rows = (
        await db["background_jobs"]
        .find(match)
        .sort("created_ts", -1)
        .to_list(length=100)
    )
    docs = (
        await db["knowledge_documents"]
        .find({**match, "status": {"$ne": "deleted"}})
        .sort("updated_at", -1)
        .to_list(length=100)
    )
    grants = (
        await db["mcp_grants"].find(match).sort("created_ts", -1).to_list(length=30)
    )
    tasks = await db["tasks"].find(match).sort("created_at", -1).to_list(length=200)
    return {
        "enabled": settings.background_jobs_enabled,
        "durable": not isinstance(db, InMemoryDatabase),
        "worker_heartbeat": getattr(request.app.state, "worker_heartbeat", None),
        "worker_error": getattr(request.app.state, "worker_error", None),
        "jobs": [jobs.public(d) for d in rows],
        "documents": [
            {k: v for k, v in d.items() if k not in {"_id", "text", "chunks"}}
            for d in docs
        ],
        "grants": [
            {k: v for k, v in d.items() if k not in {"_id", "window", "requests"}}
            for d in grants
        ],
        "tasks": [to_task_out(t).model_dump(mode="json") for t in tasks],
        "notifications": await deadlines.notifications(db, business.id),
    }


@router.post("/jobs", status_code=202)
async def submit_job(
    payload: JobIn, request: Request, business=Depends(get_owned_business)
):
    enabled()
    if payload.kind == "ceo_plan" and len(payload.goal.strip()) < 5:
        raise HTTPException(422, "Describe a goal in at least five characters")
    return await jobs.enqueue(
        request.app.state.db,
        business.id,
        business.owner_user_id,
        payload.kind,
        {"goal": payload.goal.strip()} if payload.kind == "ceo_plan" else {},
        payload.idempotency_key,
    )


@router.post("/jobs/{job_id}/{command}")
async def control_job(
    job_id: str, command: str, request: Request, business=Depends(get_owned_business)
):
    db = request.app.state.db
    job = await db["background_jobs"].find_one(
        {"job_id": job_id, "business_id": business.id}
    )
    if not job:
        raise HTTPException(404, "Job not found")
    if command == "retry":
        enabled()
        if job["status"] != "failed" or job["kind"] == "execute_task":
            raise HTTPException(409, "Only failed drafting/index jobs can be retried")
        changed = await db["background_jobs"].update_one(
            {"_id": job_id, "status": "failed"},
            {
                "$set": {
                    "status": "queued",
                    "attempts": 0,
                    "run_after": time.time(),
                    "error": None,
                }
            },
        )
        if not changed.modified_count:
            raise HTTPException(409, "Job changed")
        await jobs.wake()
    elif command == "cancel":
        if job["status"] not in {"queued", "retry_scheduled", "cancelled"}:
            raise HTTPException(409, "Running/completed work cannot be cancelled here")
        await db["background_jobs"].update_one(
            {"_id": job_id, "status": {"$in": ["queued", "retry_scheduled"]}},
            {"$set": {"status": "cancelled"}},
        )
        current = await db["background_jobs"].find_one({"_id": job_id})
        if current["status"] != "cancelled":
            raise HTTPException(409, "Job was already claimed")
        if job["kind"] == "execute_task":
            await db["tasks"].update_one(
                {
                    "business_id": business.id,
                    "task_id": job["payload"]["task_id"],
                    "status": "approved",
                },
                {"$set": {"status": "cancelled"}},
            )
        if job["kind"] == "index_document":
            await db["knowledge_documents"].update_one(
                {
                    "document_id": job["payload"]["document_id"],
                    "business_id": business.id,
                    "version": job["payload"]["version"],
                    "status": "pending",
                },
                {"$set": {"status": "cancelled"}},
            )
    else:
        raise HTTPException(422, "Unknown command")
    return jobs.public(await db["background_jobs"].find_one({"_id": job_id}))


@task_router.put("/{task_id}/deadline")
async def deadline(
    payload: DeadlineIn, request: Request, owned=Depends(get_owned_task)
):
    return to_task_out(
        await deadlines.set_deadline(
            request.app.state.db,
            owned["business"],
            owned["task"],
            owned["business"].owner_user_id,
            payload,
        )
    )


@router.post("/notifications/{notification_id}/read")
async def mark_read(
    notification_id: str, request: Request, business=Depends(get_owned_business)
):
    r = await request.app.state.db["notifications"].update_one(
        {"_id": notification_id, "business_id": business.id}, {"$set": {"read": True}}
    )
    if not r.matched_count:
        raise HTTPException(404, "Notification not found")
    return {"read": True}


@router.post("/knowledge", status_code=202)
async def document(
    payload: DocumentIn, request: Request, business=Depends(get_owned_business)
):
    enabled()
    return await knowledge.submit_document(
        request.app.state.db, business, business.owner_user_id, payload
    )


@router.delete("/knowledge/{document_id}")
async def delete_document(
    document_id: str,
    request: Request,
    version: int = Query(ge=1),
    business=Depends(get_owned_business),
):
    return await knowledge.delete_document(
        request.app.state.db, business.id, document_id, version
    )


@router.post("/knowledge/{document_id}/reindex", status_code=202)
async def reindex(
    document_id: str,
    request: Request,
    version: int = Query(ge=1),
    business=Depends(get_owned_business),
):
    enabled()
    return await knowledge.reindex_document(
        request.app.state.db, business, business.owner_user_id, document_id, version
    )


@router.post("/knowledge/search")
async def search(
    payload: SearchIn, request: Request, business=Depends(get_owned_business)
):
    return await knowledge.search(
        request.app.state.db,
        business.id,
        payload.department,
        payload.query,
        payload.limit,
    )


@router.post("/knowledge/answer")
async def answer(
    payload: SearchIn, request: Request, business=Depends(get_owned_business)
):
    return await knowledge.answer(
        request.app.state.db, business.id, payload.department, payload.query
    )


@router.post("/mcp-grants")
async def grant(
    payload: MCPGrantIn,
    request: Request,
    response: Response,
    business=Depends(get_owned_business),
    user=Depends(get_current_user),
):
    from ...mcp_server import mint

    response.headers["Cache-Control"] = "no-store"
    return await mint(request.app.state.db, business, user, payload)


@router.post("/mcp-grants/{grant_id}/revoke")
async def revoke(grant_id: str, request: Request, business=Depends(get_owned_business)):
    r = await request.app.state.db["mcp_grants"].update_one(
        {"_id": grant_id, "business_id": business.id}, {"$set": {"revoked": True}}
    )
    if not r.matched_count:
        raise HTTPException(404, "Grant not found")
    return {"revoked": True}
