"""Per-business agent runtime registry.

Agents/AgentManager are in-memory Python objects, not persisted directly —
this registry lazily creates one AgentManager per business the first time
it's touched, keyed by business_id, and holds it for the process lifetime.

Rehydration: the first time a business is touched after a restart (real
Mongo only — the in-memory Mongo fallback never survives a restart either,
so there's nothing to rehydrate from there), each agent's numeric state is
seeded from its most recent agent_snapshots document instead of the
business's onboarding baseline. This is a bounded fix, not full replay:
it trusts the latest snapshot as ground truth rather than re-running the
non-deterministic LLM-driven decision log since that snapshot, which would
be real additional scope (and couldn't be made deterministic anyway).
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ..models.business_schemas import BusinessOut
from ..models.policy_schemas import AgentPolicyOut
from ..simulation.simulation_engine import SimulationEngine
from .agent_manager import AgentManager, DEFAULT_ENABLED_AGENTS

# Fields every agent's get_status() always includes but that aren't live
# numeric state to restore — restoring "agent_id" from a stale snapshot
# would be harmless (it's derived the same way each time) but restoring
# "agent_name" is pointless churn, so both are skipped for clarity.
_NON_STATE_STATUS_KEYS = {"agent_id", "agent_name"}


@dataclass
class BusinessRuntime:
    agent_manager: AgentManager
    simulation_engine: Optional[SimulationEngine] = None
    current_run_id: Optional[str] = None
    execution_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    review_jobs: set = field(default_factory=set)


def _apply_snapshot_state(agent: Any, state: Dict[str, Any]) -> None:
    for key, value in state.items():
        if key in _NON_STATE_STATUS_KEYS:
            continue
        if hasattr(agent, key):
            setattr(agent, key, value)


class AgentRegistry:
    def __init__(self, db: Any = None):
        self._db = db
        self._runtimes: Dict[str, BusinessRuntime] = {}
        # Guards creation only (see below) — without it, two concurrent
        # first-touch requests for the same business_id could both miss the
        # cache, each build its own AgentManager and rehydrate its own copy
        # of agent state, and the second to finish would silently clobber
        # the first in self._runtimes, stranding whichever caller kept a
        # reference to the discarded one.
        self._creation_lock = asyncio.Lock()

    async def get_or_create(self, business: BusinessOut) -> BusinessRuntime:
        if business.id in self._runtimes:
            return self._runtimes[business.id]

        async with self._creation_lock:
            # Re-check: another call may have finished creating it while we
            # were waiting for the lock.
            if business.id not in self._runtimes:
                starting_state = {
                    "starting_budget": business.starting_budget,
                    "starting_customer_base": business.starting_customer_base,
                    "starting_headcount": business.starting_headcount,
                    "starting_resources": business.starting_resources,
                }
                enabled_agents = (
                    getattr(business, "enabled_agents", None) or DEFAULT_ENABLED_AGENTS
                )
                agent_manager = AgentManager(
                    business_id=business.id,
                    starting_state=starting_state,
                    enabled_agents=enabled_agents,
                )
                await self._rehydrate_from_snapshots(business.id, agent_manager)
                await self._rehydrate_policies(business.id, agent_manager)
                if self._db is not None:
                    from ..database.utils import find_one
                    from ..services.ledger import sync_finance

                    account = await find_one(
                        self._db["financial_accounts"], {"_id": business.id}
                    )
                    if account:
                        sync_finance(
                            BusinessRuntime(agent_manager=agent_manager), account
                        )
                self._runtimes[business.id] = BusinessRuntime(
                    agent_manager=agent_manager
                )
            return self._runtimes[business.id]

    async def _rehydrate_from_snapshots(
        self, business_id: str, agent_manager: AgentManager
    ) -> None:
        if self._db is None:
            return
        for agent in agent_manager.agents.values():
            cursor = (
                self._db["agent_snapshots"]
                .find({"business_id": business_id, "agent_id": agent.agent_id})
                .sort("timestamp", -1)
                .limit(1)
            )
            docs = await cursor.to_list(length=1)
            if docs:
                _apply_snapshot_state(agent, docs[0].get("state", {}))

    async def _rehydrate_policies(
        self, business_id: str, agent_manager: AgentManager
    ) -> None:
        if self._db is None:
            return
        cursor = self._db["agent_policies"].find({"business_id": business_id})
        docs = await cursor.to_list(length=100)
        for doc in docs:
            agent_key = doc.get("agent_key")
            agent = agent_manager.agents.get(agent_key)
            if agent is not None:
                policy = AgentPolicyOut(
                    enabled=doc.get("enabled", False),
                    auto_approve_max=doc.get("auto_approve_max"),
                    auto_deny_min=doc.get("auto_deny_min"),
                    updated_at=doc["updated_at"],
                )
                agent.set_policy(policy)

    async def close(self):
        jobs = {
            job for runtime in self._runtimes.values() for job in runtime.review_jobs
        }
        if jobs:
            _, pending = await asyncio.wait(jobs, timeout=5)
            for job in pending:
                job.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
