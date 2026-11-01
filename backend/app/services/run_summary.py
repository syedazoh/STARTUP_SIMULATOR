"""Deterministic run retrospective from actual task states, not proposals."""

from collections import Counter
from ..agents.schemas import RunSummary


async def summarize_tasks(db, business_id, run_id):
    tasks = (
        await db["tasks"]
        .find({"business_id": business_id, "run_id": run_id})
        .to_list(length=1001)
    )
    counts = Counter(t["status"] for t in tasks)
    terminal = {"executed", "failed", "denied", "rejected"}
    pending = sum(n for status, n in counts.items() if status not in terminal)
    settled = sum(
        (t.get("result") or {}).get("financial_amount", 0)
        for t in tasks
        if t["status"] == "executed" and t["action_type"] != "budget_request"
    )
    risks = []
    missing_receipts = sum(
        "financial_amount" not in (t.get("result") or {})
        for t in tasks
        if t["status"] == "executed" and t["action_type"] != "budget_request"
    )
    if missing_receipts:
        risks.append(
            f"{missing_receipts} executed tasks have no financial receipt; the expense total is incomplete."
        )
    if pending:
        risks.append(
            f"{pending} tasks remain pending or require reconciliation; their actions are not completed."
        )
    if counts["failed"]:
        risks.append(f"{counts['failed']} tasks failed.")
    return RunSummary(
        headline=f"{len(tasks)} proposals: {counts['executed']} executed, {pending} pending or unresolved.",
        key_decisions=[f"{status}: {count}" for status, count in sorted(counts.items())]
        + [
            f"Confirmed expenses in executed task reports: ${settled:.2f}; budget allocations are not expenses."
        ],
        risks=risks,
        recommendation="Review unresolved tasks and their execution evidence. Task execution does not prove the business goal was achieved.",
    )
