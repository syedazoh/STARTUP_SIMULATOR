"""Test RAG decision memory (Phase 4), generalized to all five agents (Phase 7)"""
import shutil
import tempfile

import pytest

from app.agents import CEOAgent, HRAgent, MarketingAgent, OperationsAgent
from app.agents.schemas import (
    ArbitrationDecision,
    HRDecision,
    MarketingDecision,
    OperationsDecision,
)
from app.config import settings
from app.rag.store import DecisionMemoryStore


@pytest.fixture
def memory_store(monkeypatch):
    tmp_dir = tempfile.mkdtemp()
    monkeypatch.setattr(settings, "chroma_persist_dir", tmp_dir)
    store = DecisionMemoryStore()
    yield store
    shutil.rmtree(tmp_dir, ignore_errors=True)


class FakeStructuredLLM:
    def __init__(self, response):
        self.response = response

    async def ainvoke(self, prompt):
        self.last_prompt = prompt
        return self.response


class TestDecisionMemoryStore:
    def test_query_similar_on_empty_store_returns_empty(self, memory_store):
        results = memory_store.query_similar("finance_001", "Budget request from Marketing for $1000", k=3)
        assert results == []

    def test_query_similar_returns_nearest_precedent(self, memory_store):
        memory_store.add_decision(
            agent_id="finance_001",
            event_type="budget_request",
            summary_text="Budget request from Marketing for $1000.00: approved (amount_approved=$1000.00). Reasoning: within budget",
            metadata={"department": "Marketing", "amount": 1000, "approved": True, "amount_approved": 1000.0},
        )
        memory_store.add_decision(
            agent_id="finance_001",
            event_type="budget_request",
            summary_text="Recruitment request from HR for 3 engineers: approved. Reasoning: growth phase justified hiring",
            metadata={"department": "HR", "amount": 0, "approved": True, "amount_approved": 0.0},
        )

        results = memory_store.query_similar("finance_001", "Budget request from Marketing for $1050.00", k=1)

        assert len(results) == 1
        assert "Marketing" in results[0]["document"]
        assert results[0]["metadata"]["department"] == "Marketing"

    def test_query_similar_filters_by_agent_id(self, memory_store):
        memory_store.add_decision(
            agent_id="finance_001",
            event_type="budget_request",
            summary_text="Budget request from Marketing for $1000.00: approved",
            metadata={"department": "Marketing"},
        )
        results = memory_store.query_similar("hr_001", "Budget request from Marketing for $1000.00", k=3)
        assert results == []


class TestGetRecent:
    def test_get_recent_on_empty_store_returns_empty(self, memory_store):
        assert memory_store.get_recent("finance_001") == []

    def test_get_recent_returns_only_that_agents_entries(self, memory_store):
        memory_store.add_decision(
            agent_id="finance_001",
            event_type="budget_request",
            summary_text="Budget request approved",
            metadata={"amount": 500},
        )
        memory_store.add_decision(
            agent_id="marketing_001",
            event_type="campaign_launch",
            summary_text="Campaign requested",
            metadata={"campaign_name": "X"},
        )
        results = memory_store.get_recent("finance_001", limit=10)
        assert len(results) == 1
        assert results[0]["document"] == "Budget request approved"
        assert results[0]["distance"] is None


@pytest.mark.asyncio
class TestAllAgentsWriteToSharedMemory:
    """Phase 7 generalized retrieve_memory/persist_memory (previously
    Finance-only) to Marketing, HR, Operations, and CEO. Each check: one
    decision persists, and a second similar request retrieves it as
    precedent context in the LLM prompt."""

    async def test_marketing_persists_and_later_retrieves_precedent(self, memory_store, monkeypatch):
        monkeypatch.setattr("app.agents.marketing_agent.get_decision_memory_store", lambda: memory_store)
        agent = MarketingAgent(agent_id="marketing_test")
        fake = FakeStructuredLLM(
            MarketingDecision(campaign_name="Spring Sale", desired_budget=3000, reasoning="Boost signups")
        )
        agent._structured_llm = fake

        await agent.process_event(
            {"type": "campaign_launch", "campaign_name": "Spring Sale", "requested_budget": 3000}
        )
        assert len(memory_store.get_recent("marketing_test")) == 1

        await agent.process_event(
            {"type": "campaign_launch", "campaign_name": "Spring Sale 2", "requested_budget": 3200}
        )
        assert "similar past decision" in fake.last_prompt.lower()
        assert len(memory_store.get_recent("marketing_test")) == 2

    async def test_hr_persists_and_later_retrieves_precedent(self, memory_store, monkeypatch):
        monkeypatch.setattr("app.agents.hr_agent.get_decision_memory_store", lambda: memory_store)
        agent = HRAgent(agent_id="hr_test")
        fake = FakeStructuredLLM(HRDecision(approved=True, headcount_approved=2, reasoning="Growth phase"))
        agent._structured_llm = fake

        await agent.process_event({"type": "recruitment_request", "role": "Engineer", "headcount": 2})
        assert len(memory_store.get_recent("hr_test")) == 1

        await agent.process_event({"type": "recruitment_request", "role": "Engineer", "headcount": 3})
        assert "similar past decision" in fake.last_prompt.lower()

    async def test_operations_persists_and_later_retrieves_precedent(self, memory_store, monkeypatch):
        monkeypatch.setattr("app.agents.operations_agent.get_decision_memory_store", lambda: memory_store)
        agent = OperationsAgent(agent_id="operations_test")
        fake = FakeStructuredLLM(
            OperationsDecision(approved=True, quantity_approved=200, reasoning="Within pool")
        )
        agent._structured_llm = fake

        await agent.process_event(
            {"type": "resource_request", "resource_type": "Cloud Compute", "quantity": 200}
        )
        assert len(memory_store.get_recent("operations_test")) == 1

        await agent.process_event(
            {"type": "resource_request", "resource_type": "Cloud Compute", "quantity": 250}
        )
        assert "similar past decision" in fake.last_prompt.lower()

    async def test_ceo_persists_and_later_retrieves_precedent(self, memory_store, monkeypatch):
        monkeypatch.setattr("app.agents.ceo_agent.get_decision_memory_store", lambda: memory_store)
        agent = CEOAgent(agent_id="ceo_test")
        fake = FakeStructuredLLM(
            ArbitrationDecision(winner="compromise", final_amount=2000, rationale="Split the difference")
        )
        agent._structured_llm = fake

        event = {
            "type": "arbitration_request",
            "finance_position": {"approved": False, "counter_proposal": 1500, "reasoning": "tight budget"},
            "marketing_position": {
                "campaign_name": "Spring Sale",
                "requested_amount": 3000,
                "reasoning": "big opportunity",
            },
            "depth": 0,
        }
        await agent.process_event(event)
        assert len(memory_store.get_recent("ceo_test")) == 1

        await agent.process_event(event)
        assert "similar past arbitration" in fake.last_prompt.lower()
