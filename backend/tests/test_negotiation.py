"""Test inter-agent negotiation / arbitration pattern (Phase 3)"""
import pytest

from app.orchestration.agent_manager import AgentManager
from app.agents.schemas import ArbitrationDecision, FinanceDecision, MarketingDecision


class FakeStructuredLLM:
    """Stand-in for ChatX.with_structured_output(...) in tests"""
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    async def ainvoke(self, prompt):
        response = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        if isinstance(response, Exception):
            raise response
        return response


class FakeMemoryStore:
    """Every agent writes to the shared DecisionMemoryStore now (Phase 7's RAG
    generalization) — faked out here so these negotiation tests don't write
    synthetic data into the real chroma_data directory."""
    def query_similar(self, agent_id, query_text, k=3):
        return []

    def add_decision(self, **kwargs):
        pass


@pytest.fixture(autouse=True)
def _fake_memory_store(monkeypatch):
    for module in ("app.agents.marketing_agent", "app.agents.ceo_agent"):
        monkeypatch.setattr(f"{module}.get_decision_memory_store", lambda: FakeMemoryStore())


@pytest.mark.asyncio
class TestNegotiation:
    async def test_campaign_approved_directly_applies_marketing_effects(self):
        mgr = AgentManager()
        finance = mgr.agents["finance"]
        marketing = mgr.agents["marketing"]

        marketing._structured_llm = FakeStructuredLLM([
            MarketingDecision(campaign_name="Spring Sale", desired_budget=3000, reasoning="Boost Q2 sign-ups")
        ])
        finance._structured_llm = FakeStructuredLLM([
            FinanceDecision(approved=True, reasoning="Well within budget", amount_approved=3000)
        ])

        starting_customers = marketing.customer_base
        starting_budget = finance.budget_pool

        await mgr.process_event("campaign_launch", {"requested_budget": 3000}, source="test")

        assert finance.budget_pool == starting_budget - 3000
        assert marketing.customer_base > starting_customers

        event_types = [e["event_type"] for e in mgr.event_bus.get_event_history()]
        assert event_types == ["campaign_launch", "budget_request", "budget_negotiation"]

    async def test_campaign_denied_escalates_to_ceo_arbitration(self):
        mgr = AgentManager()
        finance = mgr.agents["finance"]
        marketing = mgr.agents["marketing"]
        ceo = mgr.agents["ceo"]

        marketing._structured_llm = FakeStructuredLLM([
            MarketingDecision(campaign_name="Big Splash", desired_budget=200000, reasoning="Aggressive growth push")
        ])
        finance._structured_llm = FakeStructuredLLM([
            FinanceDecision(
                approved=False,
                reasoning="Exceeds available budget pool",
                amount_approved=0.0,
                counter_proposal=50000,
            )
        ])
        ceo._structured_llm = FakeStructuredLLM([
            ArbitrationDecision(
                winner="compromise",
                final_amount=50000,
                rationale="Marketing's growth case has merit but Finance's caution on cash reserves wins out partially",
            )
        ])

        starting_customers = marketing.customer_base
        starting_budget = finance.budget_pool

        await mgr.process_event("campaign_launch", {"requested_budget": 200000}, source="test")

        assert finance.budget_pool == starting_budget - 50000
        assert marketing.customer_base > starting_customers

        event_types = [e["event_type"] for e in mgr.event_bus.get_event_history()]
        assert event_types == [
            "campaign_launch",
            "budget_request",
            "budget_negotiation",
            "arbitration_request",
            "arbitration_result",
        ]

    async def test_ceo_sides_with_finance_denial_stands(self):
        mgr = AgentManager()
        finance = mgr.agents["finance"]
        marketing = mgr.agents["marketing"]
        ceo = mgr.agents["ceo"]

        marketing._structured_llm = FakeStructuredLLM([
            MarketingDecision(campaign_name="Moonshot", desired_budget=500000, reasoning="Go big or go home")
        ])
        finance._structured_llm = FakeStructuredLLM([
            FinanceDecision(
                approved=False,
                reasoning="Far exceeds available budget pool",
                amount_approved=0.0,
                counter_proposal=None,
            )
        ])
        ceo._structured_llm = FakeStructuredLLM([
            ArbitrationDecision(
                winner="finance",
                final_amount=0.0,
                rationale="Finance's concern about runway is decisive here; denial stands",
            )
        ])

        starting_customers = marketing.customer_base
        starting_budget = finance.budget_pool

        await mgr.process_event("campaign_launch", {"requested_budget": 500000}, source="test")

        assert finance.budget_pool == starting_budget
        assert marketing.customer_base == starting_customers
