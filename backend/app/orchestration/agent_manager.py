"""Agent Manager for Orchestrating Multiple Agents"""
from typing import Any, Dict, List, Optional

from ..agents import CEOAgent, FinanceAgent, HRAgent, MarketingAgent, OperationsAgent
from .event_bus import EventBus

DEFAULT_ENABLED_AGENTS = ["finance", "marketing", "hr", "operations", "ceo"]

class AgentManager:
    """Manages all agents and their interactions for one business.

    `business_id` and `starting_state` default to values that reproduce the
    original single-tenant behavior (agent_id="finance_001" etc, hardcoded
    starting numbers) so zero-arg construction stays valid for direct tests.
    """
    def __init__(
        self,
        business_id: str = "default",
        starting_state: Optional[Dict[str, Any]] = None,
        enabled_agents: Optional[List[str]] = None,
    ):
        self.business_id = business_id
        self.event_bus = EventBus()
        self.agents: Dict[str, Any] = {}
        self.starting_state = starting_state or {}
        self.enabled_agents = enabled_agents or DEFAULT_ENABLED_AGENTS
        self.initialize_agents()

    def initialize_agents(self) -> None:
        s = self.starting_state
        bid = self.business_id

        agent_constructors = {
            "finance": lambda: FinanceAgent(
                budget_pool=s.get("starting_budget", 100000.0),
                agent_id=f"finance_{bid}",
            ),
            "marketing": lambda: MarketingAgent(
                customer_base=s.get("starting_customer_base", 1000),
                agent_id=f"marketing_{bid}",
            ),
            "hr": lambda: HRAgent(
                employee_count=s.get("starting_headcount", 50),
                agent_id=f"hr_{bid}",
            ),
            "operations": lambda: OperationsAgent(
                resource_pool=s.get("starting_resources", 10000),
                agent_id=f"operations_{bid}",
            ),
            "ceo": lambda: CEOAgent(agent_id=f"ceo_{bid}"),
        }

        self.agents = {}
        for agent_key in self.enabled_agents:
            if agent_key in agent_constructors:
                self.agents[agent_key] = agent_constructors[agent_key]()

        for agent in self.agents.values():
            agent.set_event_bus(self.event_bus)

        if "finance" in self.agents:
            self.event_bus.subscribe("budget_request", self.agents["finance"].process_event)
        if "marketing" in self.agents:
            self.event_bus.subscribe("campaign_launch", self.agents["marketing"].process_event)
        if "hr" in self.agents:
            self.event_bus.subscribe("recruitment_request", self.agents["hr"].process_event)
        if "operations" in self.agents:
            self.event_bus.subscribe("resource_request", self.agents["operations"].process_event)

        # Negotiation / arbitration wiring
        if "marketing" in self.agents:
            self.event_bus.subscribe("budget_negotiation", self.agents["marketing"].process_event)
        if "ceo" in self.agents:
            self.event_bus.subscribe("arbitration_request", self.agents["ceo"].process_event)
        if "finance" in self.agents:
            self.event_bus.subscribe("arbitration_result", self.agents["finance"].process_event)
        if "marketing" in self.agents:
            self.event_bus.subscribe("arbitration_result", self.agents["marketing"].process_event)

    async def process_event(self, event_type: str, data: Dict[str, Any], source: str = "user") -> None:
        await self.event_bus.publish(event_type, data, source)

    async def trigger_action(self, agent_key: str, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fire an event and return the acting agent's own result (not just discard it),
        for manual per-agent actions where the caller needs the decision inline."""
        _, results = await self.event_bus.publish(event_type, data, source="manual")
        return results[0] if results else {"status": "no_subscriber"}

    async def get_all_agents_status(self) -> Dict[str, Any]:
        status = {}
        for agent_name, agent in self.agents.items():
            status[agent_name] = await agent.get_status()
        return status
