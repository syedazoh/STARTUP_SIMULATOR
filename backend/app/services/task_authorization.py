"""Mandatory, persisted CEO authorization before an owner/auto execution."""

from datetime import datetime, timezone
from fastapi import HTTPException
from ..database.utils import find_one
from ..models.action_schemas import validate_action
from ..core.llm_errors import report_llm_failure
from . import ledger


async def authorize(db, registry, business, task):
    runtime = await registry.get_or_create(business)
    ceo = runtime.agent_manager.agents.get("ceo")
    if ceo is None:
        raise HTTPException(
            status_code=409,
            detail="The CEO must be enabled to authorize department tasks",
        )
    verified_plan = False
    if task.get("source") == "ceo" and task.get("plan_id"):
        plan = await find_one(
            db["ceo_plans"], {"business_id": business.id, "plan_id": task["plan_id"]}
        )
        if plan and plan["status"] in {"assigning", "active", "completed"}:
            verified_plan = any(
                a["department"] == task["agent"]
                and a["action_type"] == task["action_type"]
                and validate_action(a["department"], a["action_type"], a["payload"])
                == task["payload"]
                and a["objective"] == task.get("objective")
                for a in plan["assignments"]
            )
        if not verified_plan:
            raise HTTPException(
                status_code=409,
                detail="CEO assignment does not match an authorized plan",
            )
    account = await ledger.account_for(db, business, runtime)
    allocated = sum(
        r["remaining_minor"]
        for r in account["reservations"].values()
        if r["state"] == "allocated"
        and r.get("department") in {task["agent"], "general"}
    )
    try:
        review = await ceo.authorize_task(
            task,
            {
                "verified_plan": verified_plan,
                "estimated_cost": ledger.amount(ledger.task_estimate(task)),
                "spendable": ledger.amount(ledger.available(account) + allocated),
            },
        )
    except Exception as exc:
        failure = report_llm_failure("ceo_task_authorization", exc)
        review = {
            "decision": "unavailable",
            "basis": "ai_review",
            "reason": failure.message,
        }
    approved = review["decision"] in {"approve", "escalate"}
    update = {
        "ceo_authorized": approved,
        "ceo_review": {**review, "reviewed_at": datetime.now(timezone.utc)},
    }
    await db["tasks"].update_one({"task_id": task["task_id"]}, {"$set": update})
    return {**task, **update}
