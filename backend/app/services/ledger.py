"""Single-document financial journal: integer minor units and optimistic concurrency.

All balances, holds, allocations and journal entries change in one Mongo write.
An interrupted external task keeps its hold for explicit reconciliation.
"""

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from uuid import uuid4

from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from ..database.utils import find_one

MAX_JOURNAL_ENTRIES = 5000


def minor(value):
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0:
            raise ValueError()
        return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError, TypeError, OverflowError) as exc:
        raise HTTPException(
            status_code=422, detail="Money must be finite and non-negative"
        ) from exc


def amount(value):
    return value / 100


def available(account):
    return account["cash_minor"] - account["reserved_minor"]


def entry(account, kind, value, task_id=None, event_id=None):
    if len(account["entries"]) >= MAX_JOURNAL_ENTRIES:
        raise HTTPException(
            status_code=409,
            detail="Financial journal capacity reached; archive before continuing",
        )
    account["entries"].append(
        {
            "id": str(uuid4()),
            "kind": kind,
            "amount_minor": value,
            "task_id": task_id,
            "event_id": event_id,
            "cash_minor": account["cash_minor"],
            "reserved_minor": account["reserved_minor"],
            "created_at": datetime.now(timezone.utc),
        }
    )


async def account_for(db, business, runtime):
    existing = await find_one(db["financial_accounts"], {"_id": business.id})
    if existing:
        return existing
    finance = runtime.agent_manager.agents.get("finance")
    cash = minor(finance.budget_pool if finance else business.starting_budget)
    doc = {
        "_id": business.id,
        "business_id": business.id,
        "version": 0,
        "cash_minor": cash,
        "reserved_minor": 0,
        "revenue_minor": minor(finance.revenue if finance else 0),
        "expenses_minor": minor(finance.expenses if finance else 0),
        "monthly_payroll_minor": 0,
        "reservations": {},
        "entries": [],
    }
    entry(doc, "opening", cash)
    try:
        await db["financial_accounts"].insert_one(doc)
    except DuplicateKeyError:
        return await find_one(db["financial_accounts"], {"_id": business.id})
    return doc


async def mutate(db, business, runtime, change):
    for _ in range(20):
        old = await account_for(db, business, runtime)
        new = deepcopy(old)
        changed = change(new)
        if changed is False:
            return old
        if (
            new["cash_minor"] < new["reserved_minor"]
            or min(new["cash_minor"], new["reserved_minor"]) < 0
        ):
            raise RuntimeError("Invalid financial state")
        new["version"] = old["version"] + 1
        update = {key: value for key, value in new.items() if key != "_id"}
        result = await db["financial_accounts"].find_one_and_update(
            {"_id": business.id, "version": old["version"]},
            {"$set": update},
            return_document=ReturnDocument.AFTER,
        )
        if result is not None:
            return result
    raise HTTPException(
        status_code=409, detail="Financial state changed; retry the request"
    )


def task_estimate(task):
    payload = task["payload"]
    kind = task["action_type"]
    if kind == "budget_request":
        return minor(payload["amount"])
    if kind == "campaign_launch":
        return minor(payload["requested_budget"])
    if kind == "recruitment_request":
        return minor(payload.get("monthly_salary", 3000)) * payload["headcount"]
    if kind == "resource_request":
        return minor(payload.get("unit_cost", 100)) * payload["quantity"]
    return 0


async def reserve(db, business, runtime, task):
    tid, needed = task["task_id"], task_estimate(task)

    def change(a):
        if tid in a["reservations"]:
            return False
        splits, remainder = [], needed
        # Department allocations fund actual work before unallocated cash.
        if task["action_type"] != "budget_request":
            for parent_id, allocation in a["reservations"].items():
                if allocation["state"] == "allocated" and allocation.get(
                    "department"
                ) in {task["agent"], "general"}:
                    used = min(remainder, allocation["remaining_minor"])
                    if used:
                        allocation["remaining_minor"] -= used
                        splits.append({"task_id": parent_id, "amount_minor": used})
                        remainder -= used
                    if not remainder:
                        break
        if remainder > available(a):
            raise HTTPException(
                status_code=409, detail="Insufficient unreserved funds for this task"
            )
        a["reserved_minor"] += remainder
        a["reservations"][tid] = {
            "state": "held",
            "amount_minor": needed,
            "allocation_splits": splits,
        }
        entry(a, "reserve", needed, tid)

    return await mutate(db, business, runtime, change)


async def settle(db, business, runtime, task, spent, *, allocation=False, payroll=0):
    tid = task["task_id"]

    def change(a):
        hold = a["reservations"].get(tid)
        if hold is None:
            return False
        if hold["state"] != "held":
            return False
        if spent < 0 or spent > hold["amount_minor"]:
            raise RuntimeError("Task cost exceeded its financial authorization")
        if allocation:
            a["reserved_minor"] -= hold["amount_minor"] - spent
            hold.update(
                state="allocated",
                remaining_minor=spent,
                department=task["payload"].get("department", "general").strip().lower(),
            )
            entry(a, "allocate", spent, tid)
            return
        # Restore unused allocation funding; unallocated unused money is released.
        remaining_spend, returned = spent, 0
        for split in hold["allocation_splits"]:
            used = min(remaining_spend, split["amount_minor"])
            remaining_spend -= used
            unused = split["amount_minor"] - used
            a["reservations"][split["task_id"]]["remaining_minor"] += unused
            returned += unused
        a["cash_minor"] -= spent
        a["expenses_minor"] += spent
        a["reserved_minor"] -= hold["amount_minor"] - returned
        a["monthly_payroll_minor"] += payroll
        hold.update(state="settled", spent_minor=spent)
        entry(a, "expense" if spent else "release", spent, tid)

    return await mutate(db, business, runtime, change)


async def release_allocation(db, business, runtime, task_id):
    def change(a):
        hold = a["reservations"].get(task_id)
        if hold is None or hold["state"] != "allocated":
            raise HTTPException(
                status_code=409, detail="Task has no releasable allocation"
            )
        if any(
            h["state"] == "held"
            and any(s["task_id"] == task_id for s in h.get("allocation_splits", []))
            for h in a["reservations"].values()
        ):
            raise HTTPException(
                status_code=409, detail="Allocation is funding an executing task"
            )
        released = hold["remaining_minor"]
        a["reserved_minor"] -= released
        hold.update(state="released", remaining_minor=0)
        entry(a, "release_allocation", released, task_id)

    return await mutate(db, business, runtime, change)


async def credit(db, business, runtime, value, event_id):
    def change(a):
        if any(item.get("event_id") == event_id for item in a["entries"]):
            return False
        a["cash_minor"] += value
        a["revenue_minor"] += value
        entry(a, "simulation_revenue", value, event_id=event_id)

    return await mutate(db, business, runtime, change)


def sync_finance(runtime, account):
    finance = runtime.agent_manager.agents.get("finance")
    if finance:
        finance.budget_pool = amount(available(account))
        finance.revenue = amount(account["revenue_minor"])
        finance.expenses = amount(account["expenses_minor"])


def public_account(account):
    return {
        "cash": amount(account["cash_minor"]),
        "reserved": amount(account["reserved_minor"]),
        "available": amount(available(account)),
        "revenue": amount(account["revenue_minor"]),
        "expenses": amount(account["expenses_minor"]),
        "monthly_payroll_commitment": amount(account["monthly_payroll_minor"]),
        "version": account["version"],
        "entries": list(reversed(account["entries"][-100:])),
    }
