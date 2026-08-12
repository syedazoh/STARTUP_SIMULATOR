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

from ..database.utils import find_one
from ..models.business_schemas import BusinessOut
from .persistence import record_decision, snapshot_agents

# Maps an action_type to the one payload field the auto-approval threshold is
# checked against. Mirrors the "one dominant scalar per request" shape
# AgentPolicyIn already relies on (see policy_schemas.py) — unknown
# action_types simply never qualify for auto-approval.
DOMINANT_SCALAR_FIELD = {
    "budget_request": "amount",
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
) -> Dict[str, Any]:
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

    if status == "auto_approved":
        task = await execute_task(db, agent_registry, business, task)

    return task


async def execute_task(
    db, agent_registry, business: BusinessOut, task: Dict[str, Any]
) -> Dict[str, Any]:
    """Runs the task's action through the live agent, then records the outcome.

    This is the only code path that actually applies a task's effects — the
    same guarantee that will let Phase 3 make it the only path allowed to
    touch decrypted third-party credentials.
    """
    runtime = agent_registry.get_or_create(business)
    now = datetime.now(timezone.utc)
    try:
        result = await runtime.agent_manager.trigger_action(task["agent"], task["action_type"], task["payload"])
        update = {"status": "executed", "executed_at": now, "result": result}
    except Exception as exc:
        update = {"status": "failed", "executed_at": now, "result": {"error": str(exc)}}

    await db["tasks"].update_one({"task_id": task["task_id"]}, {"$set": update})
    # Every create_task() call today originates from a manual per-agent action
    # (see agent_actions.py), so "manual" is still the accurate decision-log
    # source — revisit if a non-manual caller (e.g. a simulation tick) starts
    # creating tasks too.
    await record_decision(db, business.id, task["action_type"], task["payload"], source="manual")
    await snapshot_agents(db, business.id, runtime.agent_manager)

    return {**task, **update}
