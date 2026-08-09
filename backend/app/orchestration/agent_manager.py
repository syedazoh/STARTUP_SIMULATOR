"""Agent Manager for Orchestrating Multiple Agents"""
from typing import Any, Dict, Optional

from ..agents import CEOAgent, FinanceAgent, HRAgent, MarketingAgent, OperationsAgent
from .event_bus import EventBus

class AgentManager:
    """Manages all agents and their interactions for one business.

    `business_id` and `starting_state` default to values that reproduce the
    original single-tenant behavior (agent_id="finance_001" etc, hardcoded
    starting numbers) so zero-arg construction stays valid for direct tests.
    """
    def __init__(self, business_id: str = "default", starting_state: Optional[Dict[str, Any]] = None):
        self.business_id = business_id
        self.event_bus = EventBus()
        self.agents: Dict[str, Any] = {}
        self.starting_state = starting_state or {}
        self.initialize_agents()

    def initialize_agents(self) -> None:
        s = self.starting_state
        bid = self.business_id

        finance_agent = FinanceAgent(
            budget_pool=s.get("starting_budget", 100000.0),
            agent_id=f"finance_{bid}",
        )
        marketing_agent = MarketingAgent(
            customer_base=s.get("starting_customer_base", 1000),
            agent_id=f"marketing_{bid}",
        )
        hr_agent = HRAgent(
            employee_count=s.get("starting_headcount", 50),
            agent_id=f"hr_{bid}",
        )
        operations_agent = OperationsAgent(
            resource_pool=s.get("starting_resources", 10000),
            agent_id=f"operations_{bid}",
        )
        ceo_agent = CEOAgent(agent_id=f"ceo_{bid}")

        self.agents = {
            "finance": finance_agent,
            "marketing": marketing_agent,
            "hr": hr_agent,
            "operations": operations_agent,
            "ceo": ceo_agent,
        }

        for agent in self.agents.values():
            agent.set_event_bus(self.event_bus)

        self.event_bus.subscribe("budget_request", finance_agent.process_event)
        self.event_bus.subscribe("campaign_launch", marketing_agent.process_event)
        self.event_bus.subscribe("recruitment_request", hr_agent.process_event)
        self.event_bus.subscribe("resource_request", operations_agent.process_event)

        # Negotiation / arbitration wiring
        self.event_bus.subscribe("budget_negotiation", marketing_agent.process_event)
        self.event_bus.subscribe("arbitration_request", ceo_agent.process_event)
        self.event_bus.subscribe("arbitration_result", finance_agent.process_event)
        self.event_bus.subscribe("arbitration_result", marketing_agent.process_event)

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
