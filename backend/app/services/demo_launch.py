"""Deterministic department adapters for the dataset launch; no LLM/provider claims."""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from pymongo import ReturnDocument

from ..models.demo_dataset import Dataset
from .audit import record_audit
from .demo_dataset import department_records, digest, load_dataset, retrieve_references

RULE_VERSION = "launch-v1"


def simulate(data: Dataset, campaign_id: str, budget_minor: int):
    campaign = next((c for c in data.campaigns if c.id == campaign_id), None)
    if campaign is None:
        raise HTTPException(422, "Unknown campaign")
    product = next(p for p in data.inventory if p.id == campaign.product_id)
    goal = next(g for g in data.goals if g.id == campaign.goal_id)
    cash = (
        data.company.starting_capital_minor
        + sum(s.amount_minor for s in data.sales)
        - sum(e.amount_minor for e in data.expenses)
    )
    if budget_minor > cash:
        raise HTTPException(409, "Synthetic opening cash cannot cover campaign")
    capacity = data.company.staffed_units_per_day * campaign.duration_days
    pending = sum(
        o.quantity
        for o in data.orders
        if o.product_id == product.id and o.status == "pending"
    )
    reserved = min(pending, product.quantity, capacity)
    reach = budget_minor * campaign.reach_per_100_minor // 100
    demand = reach * campaign.conversion_bps // 10000
    fulfilled = min(demand, product.quantity - reserved, capacity - reserved)
    revenue = (fulfilled + reserved) * product.unit_price_minor
    cost_of_goods = (fulfilled + reserved) * product.unit_cost_minor
    return {
        "synthetic": True,
        "rule_version": RULE_VERSION,
        "currency": data.currency,
        "campaign_id": campaign_id,
        "budget_minor": budget_minor,
        "opening_cash_minor": cash,
        "reach": reach,
        "new_orders": demand,
        "fulfilled_units": fulfilled,
        "pending_orders_fulfilled": reserved,
        "unfulfilled_new_orders": demand - fulfilled,
        "revenue_minor": revenue,
        "cost_of_goods_minor": cost_of_goods,
        "contribution_minor": revenue - cost_of_goods - budget_minor,
        "ending_cash_minor": cash - budget_minor + revenue,
        "remaining_inventory": product.quantity - reserved - fulfilled,
        "goal_met": fulfilled >= goal.target_units
        and campaign.launch_date + timedelta(days=campaign.duration_days)
        <= goal.due_date,
    }


def fingerprint(task):
    return digest(
        {
            key: task.get(key)
            for key in (
                "business_id",
                "task_id",
                "agent",
                "action_type",
                "payload",
                "objective",
                "demo_import_id",
                "mode",
                "revision",
                "simulation_rule_version",
                "approval_expires_at",
            )
        }
    )


async def context(db, business_id, import_id):
    """All five department views share one exact immutable import digest."""
    return {
        role: {
            "data": await department_records(db, business_id, import_id, role),
            "sources": await retrieve_references(
                db,
                business_id,
                import_id,
                role,
                "launch approval inventory candidates forecasts",
            ),
        }
        for role in ("marketing", "finance", "hr", "operations", "ceo")
    }


async def review(db, business, task):
    if task["status"] not in {
        "pending_ceo_review",
        "pending_approval",
        "needs_changes",
    }:
        raise HTTPException(409, "Demo task cannot be reviewed in this state")
    payload = task["payload"]
    doc = await load_dataset(db, business.id, payload["import_id"])
    if doc["digest"] != payload["dataset_digest"]:
        raise HTTPException(409, "Dataset changed")
    data = Dataset.model_validate(doc["data"])
    campaign = next((c for c in data.campaigns if c.id == payload["campaign_id"]), None)
    if campaign is None:
        raise HTTPException(422, "Unknown campaign")
    try:
        forecast = simulate(data, campaign.id, payload["budget_minor"])
        blocked = None
    except HTTPException as exc:
        forecast, blocked = None, exc.detail
    if not all(
        role in business.enabled_agents
        for role in ("finance", "marketing", "hr", "operations", "ceo")
    ):
        raise HTTPException(409, "Enable all five departments for the launch scenario")
    views = await context(db, business.id, doc["import_id"])
    product = next(p for p in data.inventory if p.id == campaign.product_id)
    views["marketing"]["analysis"] = {
        "proposal": campaign.name,
        "budget_minor": payload["budget_minor"],
        "campaign_id": campaign.id,
    }
    views["finance"]["analysis"] = {
        "opening_cash_minor": data.company.starting_capital_minor
        + sum(r.amount_minor for r in data.sales)
        - sum(r.amount_minor for r in data.expenses),
        "review": blocked or "affordable",
        "currency": data.currency,
    }
    views["hr"]["analysis"] = {
        "staffed_units_per_day": data.company.staffed_units_per_day,
        "candidate_count": len(data.candidates),
        "note": "Applicants contribute no staff capacity; no hiring decisions made.",
    }
    views["operations"]["analysis"] = {
        "available_stock": product.quantity,
        "fulfillment_capacity": data.company.staffed_units_per_day
        * campaign.duration_days,
        "pending_units": sum(
            o.quantity
            for o in data.orders
            if o.product_id == product.id and o.status == "pending"
        ),
    }
    views["ceo"]["analysis"] = {
        "review": "blocked" if blocked else "awaiting_owner_approval",
        "goal_id": campaign.goal_id,
    }
    update = {
        "demo_import_id": doc["import_id"],
        "mode": "simulation",
        "revision": 1,
        "simulation_rule_version": RULE_VERSION,
        "approval_expires_at": (
            datetime.now(timezone.utc) + timedelta(hours=24)
        ).isoformat(),
        "ceo_authorized": blocked is None,
        "status": "blocked" if blocked else "pending_approval",
        "ceo_review": {
            "decision": "request_changes" if blocked else "approve",
            "basis": "deterministic_dataset_rules",
            "reason": blocked
            or "Finance affordability reviewed; explicit owner approval required.",
            "departments": views,
            "forecast": forecast,
            "rule_version": RULE_VERSION,
        },
    }
    update["proposal_digest"] = fingerprint({**task, **update})
    changed = await db["tasks"].find_one_and_update(
        {
            "task_id": task["task_id"],
            "business_id": business.id,
            "status": task["status"],
        },
        {"$set": update},
        return_document=ReturnDocument.AFTER,
    )
    if changed is None:
        raise HTTPException(409, "Task changed during review")
    return changed


async def validate_approval(db, business, task):
    if (
        task.get("proposal_digest") != fingerprint(task)
        or task.get("mode") != "simulation"
        or task.get("simulation_rule_version") != RULE_VERSION
    ):
        raise HTTPException(409, "Proposal changed; create a new demo proposal")
    expires = datetime.fromisoformat(task["approval_expires_at"])
    if expires <= datetime.now(timezone.utc):
        raise HTTPException(409, "Demo approval expired; create a new proposal")
    doc = await load_dataset(db, business.id, task["payload"]["import_id"])
    if doc["digest"] != task["payload"]["dataset_digest"]:
        raise HTTPException(409, "Dataset does not match proposal")
    return doc


async def execute(db, business, task):
    doc = await validate_approval(db, business, task)
    # No external actions or dataset mutation: results are isolated scenario branches.
    result = simulate(
        Dataset.model_validate(doc["data"]),
        task["payload"]["campaign_id"],
        task["payload"]["budget_minor"],
    )
    baseline_campaign = next(
        c for c in doc["data"]["campaigns"] if c["id"] == task["payload"]["campaign_id"]
    )
    baseline_blocker = None
    try:
        baseline = simulate(
            Dataset.model_validate(doc["data"]),
            baseline_campaign["id"],
            baseline_campaign["baseline_budget_minor"],
        )
    except HTTPException as exc:
        baseline, baseline_blocker = None, exc.detail
    result.update(
        {
            "baseline": baseline,
            "baseline_blocker": baseline_blocker,
            "dataset_digest": doc["digest"],
            "import_id": doc["import_id"],
            "task_id": task["task_id"],
            "proposal_digest": task["proposal_digest"],
            "ceo_report": {
                "basis": "deterministic_dataset_rules",
                "task_id": task["task_id"],
                "summary": f"Synthetic launch fulfilled {result['fulfilled_units']} new units; contribution {result['contribution_minor']} USD cents. No real transactions occurred.",
                "sources": task["ceo_review"]["departments"]["ceo"]["sources"],
            },
        }
    )
    # Compute before atomic transition: a retry cannot repeat any effect.
    changed = await db["tasks"].find_one_and_update(
        {
            "task_id": task["task_id"],
            "business_id": business.id,
            "status": "approved",
            "ceo_authorized": True,
            "proposal_digest": task["proposal_digest"],
            "payload": task["payload"],
            "approval_digest": task["proposal_digest"],
            "approved_by": business.owner_user_id,
        },
        {
            "$set": {
                "status": "executed",
                "result": result,
                "executed_at": datetime.now(timezone.utc),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if changed is None:
        raise HTTPException(
            409, "Demo needs current owner approval or was already executed"
        )
    await record_audit(
        db,
        business.owner_user_id,
        business.id,
        "demo_executed",
        target_id=task["task_id"],
    )
    return changed
