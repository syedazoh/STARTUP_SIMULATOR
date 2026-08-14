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
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..models.business_schemas import BusinessOut
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

    async def get_or_create(self, business: BusinessOut) -> BusinessRuntime:
        if business.id not in self._runtimes:
            starting_state = {
                "starting_budget": business.starting_budget,
                "starting_customer_base": business.starting_customer_base,
                "starting_headcount": business.starting_headcount,
                "starting_resources": business.starting_resources,
            }
            enabled_agents = getattr(business, "enabled_agents", None) or DEFAULT_ENABLED_AGENTS
            agent_manager = AgentManager(
                business_id=business.id,
                starting_state=starting_state,
                enabled_agents=enabled_agents,
            )
            await self._rehydrate_from_snapshots(business.id, agent_manager)
            self._runtimes[business.id] = BusinessRuntime(agent_manager=agent_manager)
        return self._runtimes[business.id]

    async def _rehydrate_from_snapshots(self, business_id: str, agent_manager: AgentManager) -> None:
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
