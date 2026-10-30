"""Shared task pipeline: create_task() and execute_task().

Every agent action that should be reviewable funnels through create_task()
instead of calling AgentManager.trigger_action() directly, so "check mode ->
maybe queue -> maybe execute" is written once here rather than once per
agent. execute_task() is the only place that runs the actual agent decision
(and, later, the only place allowed to call out to a third-party API via
credentials) — approve/auto-approve both end up here.
"""
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
    doc = await find_one(db["agent_modes"], {"business_id": business_id, "agent": agent})
    if doc is None:
        return {"mode": "manual", "auto_thresholds": {}}
    return doc


def _within_auto_threshold(action_type: str, payload: Dict[str, Any], thresholds: Dict[str, Any]) -> bool:
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
    if agent not in runtime.agent_manager.agents:
        raise HTTPException(status_code=409, detail="Department is disabled for this business")
    requires_asset = requires_asset or action_type == "reel_request"
    mode_doc = await _get_mode(db, business.id, agent)
    created_at = datetime.now(timezone.utc)

    if requires_asset:
        status = "awaiting_asset"
    elif mode_doc["mode"] == "auto" and _within_auto_threshold(action_type, payload, mode_doc["auto_thresholds"]):
        status = "auto_approved"
    else:
        status = "pending_approval"

    task = {
        "task_id": str(uuid4()),
        "source": source,
        "plan_id": plan_id,
        "run_id": run_id,
        "objective": objective,
        "success_criteria": success_criteria,
        "business_id": business.id,
        "agent": agent,
        "action_type": action_type,
        "payload": payload,
        "requires_asset": requires_asset,
        "asset_id": None,
        "status": status,
        "owner_feedback": None,
        "result": None,
        "created_at": created_at,
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
        details={"agent": agent, "action_type": action_type, "status": status},
    )

    if status == "auto_approved":
        task = await execute_task(db, agent_registry, business, task)

    return task


async def execute_task(
    db, agent_registry, business: BusinessOut, task: Dict[str, Any]
) -> Dict[str, Any]:
    """Atomically claim work before applying effects; terminal failures are not retried.

    An interrupted external call remains `executing` for reconciliation. It must
    never be automatically retried: the provider may have accepted the call.
    """
    claimed = await db["tasks"].find_one_and_update(
        {"task_id": task["task_id"], "business_id": business.id,
         "status": {"$in": ["approved", "auto_approved"]}},
        {"$set": {"status": "executing"}}, return_document=ReturnDocument.AFTER,
    )
    if claimed is None:
        raise HTTPException(status_code=409, detail="Task is not eligible for execution")

    runtime = await agent_registry.get_or_create(business)
    async with runtime.execution_lock:
        before = await runtime.agent_manager.get_all_agents_status()
        try:
            handler = EXTERNAL_ACTION_HANDLERS.get(claimed["action_type"])
            if handler is not None:
                result = await handler(db, business, claimed["payload"])
            else:
                result = await runtime.agent_manager.trigger_action(
                    claimed["agent"], claimed["action_type"], claimed["payload"])
            outcome = result.get("status")
            if outcome in {"failed", "no_subscriber", "unknown_event"}:
                status = "failed"
            elif outcome in {"denied", "campaign_denied"}:
                status = "denied"
            else:
                status = "executed"
        except Exception:
            # Do not expose exception strings that may contain provider secrets.
            import logging
            logging.getLogger(__name__).warning("Task execution failed: %s", claimed["task_id"])
            result, status = {"status": "failed", "reason": "execution_error"}, "failed"

        now = datetime.now(timezone.utc)
        update = {"status": status, "executed_at": now, "result": result}
        await db["tasks"].update_one({"task_id": claimed["task_id"]}, {"$set": update})
        completed = {**claimed, **update}
        await record_decision(db, business.id, claimed["action_type"],
                              {"payload": claimed["payload"], "result": result, "task_id": claimed["task_id"]},
                              source=claimed.get("source", "manual"), run_id=claimed.get("run_id"))
        await snapshot_agents(db, business.id, runtime.agent_manager)
        from .supervision import report_task
        await report_task(db, business, runtime, completed, before)
        return completed
