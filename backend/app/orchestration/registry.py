"""Per-business agent runtime registry.

Agents/AgentManager are in-memory Python objects, not persisted directly —
this registry lazily creates one AgentManager per business the first time
it's touched, keyed by business_id, and holds it for the process lifetime.

Rehydration is intentionally NOT implemented: a restart resets every
business's live numeric state back to its onboarding baseline, even under
real Mongo. Historical decision_logs/agent_snapshots are retained for
display, just not replayed into memory — full replay would mean either
replaying a non-deterministic LLM-driven decision log or trusting a single
snapshot as ground truth, both real additional scope beyond this pass.
"""
from dataclasses import dataclass
from typing import Dict, Optional

from ..models.business_schemas import BusinessOut
from ..simulation.simulation_engine import SimulationEngine
from .agent_manager import AgentManager


@dataclass
class BusinessRuntime:
    agent_manager: AgentManager
    simulation_engine: Optional[SimulationEngine] = None
    current_run_id: Optional[str] = None


class AgentRegistry:
    def __init__(self):
        self._runtimes: Dict[str, BusinessRuntime] = {}

    def get_or_create(self, business: BusinessOut) -> BusinessRuntime:
        if business.id not in self._runtimes:
            starting_state = {
                "starting_budget": business.starting_budget,
                "starting_customer_base": business.starting_customer_base,
                "starting_headcount": business.starting_headcount,
                "starting_resources": business.starting_resources,
            }
            self._runtimes[business.id] = BusinessRuntime(
                agent_manager=AgentManager(business_id=business.id, starting_state=starting_state)
            )
        return self._runtimes[business.id]
