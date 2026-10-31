"""CEO assignment lifecycle. All effects still use the shared approval pipeline."""

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from pymongo import ReturnDocument

from ..database.utils import find_one
from ..models.supervision_schemas import CEOPlan
from ..core.llm_errors import report_llm_failure
from .audit import record_audit


async def propose_plan(db, registry, business, goal):
    runtime = await registry.get_or_create(business)
    ceo = runtime.agent_manager.agents.get("ceo")
    if ceo is None:
        raise HTTPException(
            status_code=409, detail="Enable the CEO agent to create a plan"
        )
    context = {
        "departments": await runtime.agent_manager.get_all_agents_status(),
        "profile": await find_one(
            db["business_profiles"], {"business_id": business.id}
        ),
    }
    try:
        plan = CEOPlan.model_validate(await ceo.create_plan(goal, context))
    except Exception as exc:
        failure = report_llm_failure("ceo_plan", exc)
        raise HTTPException(
            status_code=503,
            detail=failure.message,
        ) from exc
    if any(a.department not in runtime.agent_manager.agents for a in plan.assignments):
        raise HTTPException(
            status_code=422, detail="Plan assigns work to a disabled department"
        )
    doc = {
        "plan_id": str(uuid4()),
        "business_id": business.id,
        "goal": goal,
        **plan.model_dump(),
        "status": "draft",
        "created_at": datetime.now(timezone.utc),
    }
    await db["ceo_plans"].insert_one(doc)
    await record_audit(
        db,
        business.owner_user_id,
        business.id,
        "ceo_plan_proposed",
        target_id=doc["plan_id"],
    )
    return {k: v for k, v in doc.items() if k != "_id"}


async def activate_plan(db, registry, business, plan_id):
    plan = await db["ceo_plans"].find_one_and_update(
        {"business_id": business.id, "plan_id": plan_id, "status": "draft"},
        {"$set": {"status": "assigning"}},
        return_document=ReturnDocument.AFTER,
    )
    if plan is None:
        raise HTTPException(
            status_code=409, detail="Plan is missing or already activated"
        )
    from .tasks import create_task

    task_ids = []
    try:
        for assignment in plan["assignments"]:
            task = await create_task(
                db,
                registry,
                business,
                assignment["department"],
                assignment["action_type"],
                assignment["payload"],
                source="ceo",
                plan_id=plan_id,
                objective=assignment["objective"],
                success_criteria=assignment["success_criteria"],
            )
            task_ids.append(task["task_id"])
    except Exception:
        # Never replay a partially assigned plan; some tasks may already have run.
        await db["ceo_plans"].update_one(
            {"plan_id": plan_id},
            {"$set": {"status": "assignment_failed", "task_ids": task_ids}},
        )
        raise HTTPException(
            status_code=409,
            detail="Plan assignment interrupted. Review its existing tasks before creating another plan.",
        )
    tasks = (
        await db["tasks"]
        .find({"business_id": business.id, "plan_id": plan_id})
        .to_list(length=12)
    )
    terminal = {"executed", "failed", "denied", "rejected"}
    status = (
        "completed"
        if len(tasks) == len(plan["assignments"])
        and all(t["status"] in terminal for t in tasks)
        else "active"
    )
    update = {"status": status, "task_ids": task_ids}
    await db["ceo_plans"].update_one({"plan_id": plan_id}, {"$set": update})
    await record_audit(
        db, business.owner_user_id, business.id, "ceo_plan_activated", target_id=plan_id
    )
    return {k: v for k, v in {**plan, **update}.items() if k != "_id"}


async def report_task(db, business, runtime, task, before):
    after = await runtime.agent_manager.get_all_agents_status()
    report = {
        "report_id": str(uuid4()),
        "business_id": business.id,
        "plan_id": task.get("plan_id"),
        "task_id": task["task_id"],
        "department": task["agent"],
        "status": task["status"],
        "objective": task.get("objective") or task["action_type"],
        "success_criteria": task.get("success_criteria"),
        "result": task.get("result"),
        "owner_feedback": task.get("owner_feedback"),
        "finance_before": before.get("finance", {}),
        "finance_after": after.get("finance", {}),
        "before": before.get(task["agent"], {}),
        "after": after.get(task["agent"], {}),
        "created_at": datetime.now(timezone.utc),
        "review_status": "pending",
    }
    # Persist evidence before an optional model call, so outages don't lose it.
    await db["department_reports"].insert_one(report)
    await schedule_pending_reviews(db, business, runtime)
    await record_audit(
        db,
        business.owner_user_id,
        business.id,
        "department_reported",
        target_id=task["task_id"],
    )

    if task.get("plan_id"):
        plan = await find_one(
            db["ceo_plans"], {"business_id": business.id, "plan_id": task["plan_id"]}
        )
        tasks = (
            await db["tasks"]
            .find({"business_id": business.id, "plan_id": task["plan_id"]})
            .to_list(length=12)
        )
        if (
            plan
            and plan["status"] == "active"
            and len(tasks) == len(plan["assignments"])
            and all(
                t["status"] in {"executed", "failed", "denied", "rejected"}
                for t in tasks
            )
        ):
            await db["ceo_plans"].update_one(
                {"plan_id": task["plan_id"]}, {"$set": {"status": "completed"}}
            )


async def schedule_pending_reviews(db, business, runtime):
    """Recover pending or expired review leases when work/reports are accessed."""
    if "ceo" not in runtime.agent_manager.agents:
        return
    slots = max(0, 4 - len(runtime.review_jobs))
    if not slots:
        return
    docs = (
        await db["department_reports"]
        .find(
            {
                "business_id": business.id,
                "review_status": {"$in": ["pending", "reviewing"]},
            }
        )
        .sort("created_at", 1)
        .to_list(length=100)
    )
    now = datetime.now(timezone.utc).timestamp()
    for doc in docs:
        if len(runtime.review_jobs) >= 4:
            break
        if (
            doc["review_status"] == "reviewing"
            and doc.get("review_lease_until", 0) > now
        ):
            continue
        lease = str(uuid4())
        claimed = await db["department_reports"].find_one_and_update(
            {
                "report_id": doc["report_id"],
                "review_status": doc["review_status"],
                **(
                    {"review_lease": doc.get("review_lease")}
                    if doc["review_status"] == "reviewing"
                    else {}
                ),
            },
            {
                "$set": {
                    "review_status": "reviewing",
                    "review_lease": lease,
                    "review_lease_until": now + 60,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if claimed:
            job = asyncio.create_task(_review_report(db, runtime, claimed, lease))
            runtime.review_jobs.add(job)
            job.add_done_callback(runtime.review_jobs.discard)


async def _review_report(db, runtime, report, lease):
    try:
        review = await asyncio.wait_for(
            runtime.agent_manager.agents["ceo"].process_event(
                {
                    "type": "department_report",
                    "report": {k: v for k, v in report.items() if k != "_id"},
                }
            ),
            timeout=20,
        )
    except asyncio.CancelledError:
        raise
    except Exception:
        review = {
            "assessment": "Execution evidence saved; narrative review unavailable.",
            "next_action": "owner_attention",
            "recommendation": "Review the recorded result.",
        }
    await db["department_reports"].update_one(
        {"report_id": report["report_id"], "review_lease": lease},
        {"$set": {"review_status": "completed", "ceo_review": review}},
    )
