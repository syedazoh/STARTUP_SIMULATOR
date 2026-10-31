"""Shared task pipeline: create_task() and execute_task().

Every agent action that should be reviewable funnels through create_task()
instead of calling AgentManager.trigger_action() directly, so "check mode ->
maybe queue -> maybe execute" is written once here rather than once per
agent. execute_task() is the only place that runs the actual agent decision
(and, later, the only place allowed to call out to a third-party API via
credentials) — approve/auto-approve both end up here.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import HTTPException
from pymongo import ReturnDocument
from ..database.utils import find_one
from ..models.action_schemas import validate_action
from ..models.business_schemas import BusinessOut
from .audit import record_audit
from .persistence import record_decision, snapshot_agents
from .social import post_to_instagram

# Maps an action_type to the one payload field the auto-approval threshold is
# checked against. Mirrors the "one dominant scalar per request" shape
# AgentPolicyIn already relies on (see policy_schemas.py) — unknown
# action_types simply never qualify for auto-approval. instagram_post has no
# entry on purpose: a social post has no numeric scalar to threshold against,
# so it always lands in pending_approval regardless of the agent's mode.
DOMINANT_SCALAR_FIELD = {
    "budget_request": "amount",
    "campaign_launch": "requested_budget",
    "recruitment_request": "headcount",
    "resource_request": "quantity",
}

# action_types with a real external side effect route through a dedicated
# handler instead of AgentManager.trigger_action's simulated-decision path.
# Each handler is the only code allowed to use a decrypted vault credential
# (see services/credentials.py's get_decrypted_token).
EXTERNAL_ACTION_HANDLERS = {
    "instagram_post": post_to_instagram,
    "reel_request": post_to_instagram,
}


async def _get_mode(db, business_id: str, agent: str) -> Dict[str, Any]:
    doc = await find_one(
        db["agent_modes"], {"business_id": business_id, "agent": agent}
    )
    if doc is None:
        return {"mode": "manual", "auto_thresholds": {}}
    return doc


def _within_auto_threshold(
    action_type: str, payload: Dict[str, Any], thresholds: Dict[str, Any]
) -> bool:
    field = DOMINANT_SCALAR_FIELD.get(action_type)
    if field is None:
        return False
    value = payload.get(field)
    max_allowed = thresholds.get("auto_approve_max")
    if value is None or max_allowed is None:
        return False
    return value <= max_allowed


async def create_task(
    db,
    agent_registry,
    business: BusinessOut,
    agent: str,
    action_type: str,
    payload: Dict[str, Any],
    requires_asset: bool = False,
    user_id: Optional[str] = None,
    source: str = "manual",
    plan_id: Optional[str] = None,
    run_id: Optional[str] = None,
    objective: Optional[str] = None,
    success_criteria: Optional[str] = None,
) -> Dict[str, Any]:
    try:
        payload = validate_action(agent, action_type, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid action payload") from exc
    runtime = await agent_registry.get_or_create(business)
    if (
        agent not in runtime.agent_manager.agents
        or "ceo" not in runtime.agent_manager.agents
    ):
        raise HTTPException(
            status_code=409, detail="Enable the department and CEO before creating work"
        )
    task = {
        "task_id": str(uuid4()),
        "source": source,
        "plan_id": plan_id,
        "run_id": run_id,
        "objective": objective or action_type.replace("_", " "),
        "success_criteria": success_criteria,
        "business_id": business.id,
        "agent": agent,
        "action_type": action_type,
        "payload": payload,
        "requires_asset": requires_asset or action_type == "reel_request",
        "asset_id": None,
        "status": "pending_ceo_review",
        "ceo_authorized": False,
        "ceo_review": None,
        "owner_feedback": None,
        "result": None,
        "created_at": datetime.now(timezone.utc),
        "decided_at": None,
        "executed_at": None,
    }
    await db["tasks"].insert_one(task)
    await record_audit(
        db,
        user_id or business.owner_user_id,
        business.id,
        "task_created",
        target_id=task["task_id"],
        details={"agent": agent, "source": source, "status": task["status"]},
    )
    return await review_task(db, agent_registry, business, task)


async def review_task(db, registry, business, task, allow_auto=True):
    from .task_authorization import authorize

    recovering = task["status"] == "ceo_reviewing"
    if (
        recovering
        and task.get("review_lease_until", 0) > datetime.now(timezone.utc).timestamp()
    ):
        raise HTTPException(
            status_code=409,
            detail="CEO review is still running; retry after one minute",
        )
    if task["status"] not in {
        "pending_ceo_review",
        "needs_revision",
        "pending_approval",
        "needs_changes",
        "ceo_reviewing",
    }:
        raise HTTPException(
            status_code=409, detail="Task is not eligible for CEO review"
        )
    claim = await db["tasks"].find_one_and_update(
        {
            "task_id": task["task_id"],
            "business_id": business.id,
            "status": task["status"],
            **(
                {"review_lease_until": task.get("review_lease_until")}
                if recovering
                else {}
            ),
        },
        {
            "$set": {
                "status": "ceo_reviewing",
                "ceo_authorized": False,
                "review_lease_until": datetime.now(timezone.utc).timestamp() + 60,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if claim is None:
        raise HTTPException(
            status_code=409, detail="Task changed or is already being reviewed"
        )
    try:
        task = await asyncio.wait_for(
            authorize(db, registry, business, claim), timeout=25
        )
    except (Exception, asyncio.CancelledError):
        await db["tasks"].update_one(
            {"task_id": task["task_id"], "status": "ceo_reviewing"},
            {"$set": {"status": "pending_ceo_review"}},
        )
        raise
    decision = task["ceo_review"]["decision"]
    if decision == "reject":
        status = "rejected"
    elif decision == "request_changes":
        status = "needs_revision"
    elif not task["ceo_authorized"]:
        status = "pending_ceo_review"
    elif task["requires_asset"] and not task.get("asset_id"):
        status = "awaiting_asset"
    else:
        mode = await _get_mode(db, business.id, task["agent"])
        auto = (
            allow_auto
            and decision != "escalate"
            and mode["mode"] == "auto"
            and _within_auto_threshold(
                task["action_type"], task["payload"], mode["auto_thresholds"]
            )
        )
        status = "auto_approved" if auto else "pending_approval"
    await db["tasks"].update_one(
        {"task_id": task["task_id"]}, {"$set": {"status": status}}
    )
    task = {**task, "status": status}
    await record_audit(
        db,
        business.owner_user_id,
        business.id,
        "ceo_task_reviewed",
        target_id=task["task_id"],
        details={"decision": decision, "basis": task["ceo_review"]["basis"]},
    )
    if status == "auto_approved":
        return await execute_task(db, registry, business, task)
    if status == "rejected":
        runtime = await registry.get_or_create(business)
        from .supervision import report_task

        await report_task(
            db,
            business,
            runtime,
            task,
            await runtime.agent_manager.get_all_agents_status(),
        )
    return task


async def execute_task(
    db, agent_registry, business: BusinessOut, task: Dict[str, Any]
) -> Dict[str, Any]:
    from . import ledger

    claimed = await db["tasks"].find_one_and_update(
        {
            "task_id": task["task_id"],
            "business_id": business.id,
            "ceo_authorized": True,
            "status": {"$in": ["approved", "auto_approved"]},
        },
        {"$set": {"status": "executing"}},
        return_document=ReturnDocument.AFTER,
    )
    if claimed is None:
        raise HTTPException(
            status_code=409,
            detail="Task needs CEO authorization and final approval before execution",
        )
    runtime = await agent_registry.get_or_create(business)
    async with runtime.execution_lock:
        account = await ledger.account_for(db, business, runtime)
        ledger.sync_finance(runtime, account)
        before = await runtime.agent_manager.get_all_agents_status()
        try:
            account = await ledger.reserve(db, business, runtime, claimed)
        except HTTPException as exc:
            if exc.status_code != 409:
                raise
            result, status = {"status": "denied", "reason": exc.detail}, "denied"
        else:
            finance = runtime.agent_manager.agents.get("finance")
            # Finance may spend this task's hold, but not another task's funds.
            spendable = ledger.amount(
                ledger.available(account)
                + account["reservations"][claimed["task_id"]]["amount_minor"]
            )
            if finance:
                finance.budget_pool = spendable
            try:
                handler = EXTERNAL_ACTION_HANDLERS.get(claimed["action_type"])
                if handler:
                    result = await handler(db, business, claimed["payload"])
                else:
                    result = await runtime.agent_manager.trigger_action(
                        claimed["agent"], claimed["action_type"], claimed["payload"]
                    )
                outcome = result.get("status")
                status = (
                    "failed"
                    if outcome in {"failed", "no_subscriber", "unknown_event"}
                    else (
                        "denied"
                        if outcome in {"denied", "campaign_denied"}
                        else "executed"
                    )
                )
            except Exception:
                result, status = {
                    "status": "failed",
                    "reason": "execution_error",
                }, "failed"
            if status == "failed" and handler is None:
                for key, snapshot in before.items():
                    for field, value in snapshot.items():
                        if isinstance(value, (int, float)) and hasattr(
                            runtime.agent_manager.agents[key], field
                        ):
                            setattr(runtime.agent_manager.agents[key], field, value)
            spent, payroll = 0, 0
            if status == "executed":
                kind, payload = claimed["action_type"], claimed["payload"]
                if kind == "budget_request":
                    spent = ledger.minor(result.get("amount_approved", 0))
                elif kind == "campaign_launch":
                    spent = (
                        ledger.minor(max(spendable - finance.budget_pool, 0))
                        if finance
                        else 0
                    )
                elif kind == "recruitment_request":
                    spent = ledger.minor(
                        payload.get("monthly_salary", 3000)
                    ) * result.get("headcount_approved", 0)
                    payroll = spent
                elif kind == "resource_request":
                    spent = ledger.minor(payload.get("unit_cost", 100)) * result.get(
                        "quantity_approved", 0
                    )
            try:
                account = await ledger.settle(
                    db,
                    business,
                    runtime,
                    claimed,
                    spent,
                    allocation=status == "executed"
                    and claimed["action_type"] == "budget_request",
                    payroll=payroll,
                )
            except Exception:
                status, result = "reconciliation_required", {
                    "status": "failed",
                    "reason": "Financial settlement interrupted; reserved funds retained for reconciliation",
                }
            result["financial_amount"] = ledger.amount(spent)
        ledger.sync_finance(runtime, account)
        update = {
            "status": status,
            "executed_at": datetime.now(timezone.utc),
            "result": result,
        }
        await db["tasks"].update_one({"task_id": claimed["task_id"]}, {"$set": update})
        completed = {**claimed, **update}
        await record_decision(
            db,
            business.id,
            claimed["action_type"],
            {
                "payload": claimed["payload"],
                "result": result,
                "task_id": claimed["task_id"],
            },
            source=claimed.get("source", "manual"),
            run_id=claimed.get("run_id"),
        )
        await snapshot_agents(db, business.id, runtime.agent_manager)
        from .supervision import report_task

        await report_task(db, business, runtime, completed, before)
        return completed
