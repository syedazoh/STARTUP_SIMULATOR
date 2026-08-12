"""Task (approval pipeline) routes.

Two routers because the URL shapes genuinely differ: listing is
business-scoped (a business's approval queue), while deciding on a task is
addressed by task id alone — the task already carries its business_id, and
get_owned_task resolves ownership from that instead of a path param.
"""
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from ..deps import get_owned_business, get_owned_task
from ...models.business_schemas import BusinessOut
from ...models.media_asset_schemas import MediaAssetOut
from ...models.task_schemas import TaskDecisionIn, TaskOut, to_task_out
from ...services.media_assets import upload_asset
from ...services.tasks import execute_task

router = APIRouter(prefix="/api/businesses/{business_id}/tasks", tags=["tasks"])
task_actions_router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# A task can only be decided while it's actually waiting on the owner.
DECIDABLE_STATUSES = {"pending_approval", "needs_changes"}


@router.get("", response_model=List[TaskOut])
async def list_tasks(
    request: Request,
    business: BusinessOut = Depends(get_owned_business),
    task_status: Optional[str] = None,
):
    query = {"business_id": business.id}
    if task_status is not None:
        query["status"] = task_status
    cursor = request.app.state.db["tasks"].find(query).sort("created_at", -1)
    docs = await cursor.to_list(length=200)
    return [to_task_out(d) for d in docs]


@task_actions_router.post("/{task_id}/approve", response_model=TaskOut)
async def approve_task(request: Request, owned: dict = Depends(get_owned_task)):
    task, business = owned["task"], owned["business"]
    if task["status"] not in DECIDABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Task is {task['status']}, not awaiting approval"
        )

    db = request.app.state.db
    decided_at = datetime.now(timezone.utc)
    await db["tasks"].update_one({"task_id": task["task_id"]}, {"$set": {"status": "approved", "decided_at": decided_at}})
    task = {**task, "status": "approved", "decided_at": decided_at}

    executed = await execute_task(db, request.app.state.agent_registry, business, task)
    return to_task_out(executed)


@task_actions_router.post("/{task_id}/reject", response_model=TaskOut)
async def reject_task(payload: TaskDecisionIn, request: Request, owned: dict = Depends(get_owned_task)):
    task, business = owned["task"], owned["business"]
    if task["status"] not in DECIDABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Task is {task['status']}, not awaiting approval"
        )

    db = request.app.state.db
    decided_at = datetime.now(timezone.utc)
    update = {"status": "rejected", "owner_feedback": payload.owner_feedback, "decided_at": decided_at}
    await db["tasks"].update_one({"task_id": task["task_id"]}, {"$set": update})
    return to_task_out({**task, **update})


@task_actions_router.post("/{task_id}/request-changes", response_model=TaskOut)
async def request_changes(payload: TaskDecisionIn, request: Request, owned: dict = Depends(get_owned_task)):
    task, business = owned["task"], owned["business"]
    if task["status"] not in DECIDABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Task is {task['status']}, not awaiting approval"
        )

    db = request.app.state.db
    decided_at = datetime.now(timezone.utc)
    update = {"status": "needs_changes", "owner_feedback": payload.owner_feedback, "decided_at": decided_at}
    await db["tasks"].update_one({"task_id": task["task_id"]}, {"$set": update})
    return to_task_out({**task, **update})


def _to_media_asset_out(doc: dict) -> MediaAssetOut:
    return MediaAssetOut(
        id=doc["asset_id"],
        business_id=doc["business_id"],
        task_id=doc["task_id"],
        uploaded_by=doc.get("uploaded_by", "owner"),
        media_type=doc["media_type"],
        agent_review=doc.get("agent_review", {}),
        uploaded_at=doc["uploaded_at"],
    )


@task_actions_router.post("/{task_id}/assets", response_model=MediaAssetOut)
async def upload_task_asset(
    request: Request,
    media_type: str = Form(...),
    file: UploadFile = File(...),
    owned: dict = Depends(get_owned_task),
):
    task = owned["task"]
    if task["status"] != "awaiting_asset":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Task is {task['status']}, not awaiting an asset"
        )

    content = await file.read()
    doc = await upload_asset(request.app.state.db, task["business_id"], task, file.filename, content, media_type)
    return _to_media_asset_out(doc)
