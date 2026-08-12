"""Admin routes — read-only aggregate views across all businesses.

Every route here is gated by require_admin, which reads role from the
DB-backed user object (deps.py), never a client-supplied value. No route
in this module — or anywhere in the codebase — imports
services/credentials.py's get_decrypted_token or queries the `credentials`
collection; that's a property of what this module was written to touch,
not a permissions check a future route could accidentally bypass. See
tests/test_admin.py for the explicit check that a connected credential's
secret never appears in any admin response.
"""
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request

from ..deps import require_admin
from ...database.mongodb import ping_mongo
from ...database.utils import find_one
from ...models.admin_schemas import AdminBusinessDetailOut, AdminBusinessSummaryOut, AdminSystemHealthOut
from ...models.auth_schemas import UserOut

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def _latest_simulation_status(db, business_id: str) -> str:
    cursor = db["simulation_runs"].find({"business_id": business_id}).sort("started_at", -1).limit(1)
    docs = await cursor.to_list(length=1)
    return docs[0]["status"] if docs else "never_run"


async def _task_status_counts(db, business_id: str) -> Dict[str, int]:
    tasks = await db["tasks"].find({"business_id": business_id}).to_list(length=1000)
    counts: Dict[str, int] = {}
    for task in tasks:
        counts[task["status"]] = counts.get(task["status"], 0) + 1
    return counts


@router.get("/businesses", response_model=List[AdminBusinessSummaryOut])
async def list_all_businesses(request: Request, admin: UserOut = Depends(require_admin)):
    db = request.app.state.db
    businesses = await db["businesses"].find({}).to_list(length=500)

    summaries = []
    for biz in businesses:
        owner = await find_one(db["users"], {"user_id": biz["owner_user_id"]})
        task_counts = await _task_status_counts(db, biz["business_id"])
        summaries.append(
            AdminBusinessSummaryOut(
                id=biz["business_id"],
                company_name=biz["company_name"],
                industry=biz["industry"],
                owner_email=owner["email"] if owner else "unknown",
                created_at=biz["created_at"],
                simulation_status=await _latest_simulation_status(db, biz["business_id"]),
                task_count=sum(task_counts.values()),
                pending_task_count=task_counts.get("pending_approval", 0),
            )
        )
    return summaries


@router.get("/businesses/{business_id}", response_model=AdminBusinessDetailOut)
async def get_business_detail(business_id: str, request: Request, admin: UserOut = Depends(require_admin)):
    db = request.app.state.db
    biz = await find_one(db["businesses"], {"business_id": business_id})
    if biz is None:
        raise HTTPException(status_code=404, detail="Business not found")

    owner = await find_one(db["users"], {"user_id": biz["owner_user_id"]})
    decisions = await db["decision_logs"].find({"business_id": business_id}).to_list(length=1000)

    return AdminBusinessDetailOut(
        id=biz["business_id"],
        company_name=biz["company_name"],
        industry=biz["industry"],
        owner_email=owner["email"] if owner else "unknown",
        created_at=biz["created_at"],
        starting_budget=biz["starting_budget"],
        starting_customer_base=biz["starting_customer_base"],
        starting_headcount=biz["starting_headcount"],
        starting_resources=biz["starting_resources"],
        simulation_status=await _latest_simulation_status(db, business_id),
        decision_count=len(decisions),
        task_status_counts=await _task_status_counts(db, business_id),
    )


@router.get("/system-health", response_model=AdminSystemHealthOut)
async def get_system_health(request: Request, admin: UserOut = Depends(require_admin)):
    db = request.app.state.db
    businesses = await db["businesses"].find({}).to_list(length=10000)
    users = await db["users"].find({}).to_list(length=10000)
    runs = await db["simulation_runs"].find({"status": "running"}).to_list(length=10000)

    return AdminSystemHealthOut(
        mongo_connected=await ping_mongo(),
        business_count=len(businesses),
        user_count=len(users),
        running_simulation_count=len(runs),
    )
