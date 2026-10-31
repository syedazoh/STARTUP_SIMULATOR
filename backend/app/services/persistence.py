"""Business-scoped Mongo persistence helpers.

Shared by the simulation engine's on_decision/on_complete hooks
(backend/app/api/routes/simulation.py) and the manual agent-action routes
(backend/app/api/routes/agent_actions.py) so both paths write decisions and
snapshots the same way.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional


async def record_decision(
    db,
    business_id: str,
    event_type: str,
    data: Dict[str, Any],
    source: str,
    run_id: Optional[str] = None,
    tick: Optional[int] = None,
) -> None:
    await db["decision_logs"].insert_one({
        "business_id": business_id,
        "simulation_run_id": run_id,
        "tick": tick,
        "event_type": event_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc),
        "source": source,
    })


async def snapshot_agents(db, business_id: str, agent_manager, run_id: Optional[str] = None) -> None:
    statuses = await agent_manager.get_all_agents_status()
    from ..database.utils import find_one
    from .ledger import amount, available
    account = await find_one(db["financial_accounts"], {"_id": business_id})
    if account and "finance" in statuses:
        statuses["finance"].update(budget_pool=amount(available(account)),
            revenue=amount(account["revenue_minor"]), expenses=amount(account["expenses_minor"]))
    now = datetime.now(timezone.utc)
    snapshots = [
        {
            "business_id": business_id,
            "simulation_run_id": run_id,
            "agent_id": status.get("agent_id", key),
            "state": status,
            "timestamp": now,
        }
        for key, status in statuses.items()
    ]
    if snapshots:
        await db["agent_snapshots"].insert_many(snapshots)
