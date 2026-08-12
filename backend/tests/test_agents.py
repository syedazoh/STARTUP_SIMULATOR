"""Test Agent Implementations"""
import pytest
import pytest_asyncio
from app.agents import FinanceAgent, HRAgent, OperationsAgent
from app.agents.schemas import FinanceDecision, HRDecision, OperationsDecision


class FakeStructuredLLM:
    """Stand-in for ChatGroq.with_structured_output(...) in tests"""
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
    generalization) — faked out here so these agent-level tests don't write
    synthetic data into the real chroma_data directory."""
    def query_similar(self, agent_id, query_text, k=3):
        return []

    def add_decision(self, **kwargs):
        pass


@pytest.fixture(autouse=True)
def _fake_memory_store(monkeypatch):
    for module in ("app.agents.hr_agent", "app.agents.operations_agent"):
        monkeypatch.setattr(f"{module}.get_decision_memory_store", lambda: FakeMemoryStore())


@pytest.mark.asyncio
class TestFinanceAgent:
    @pytest_asyncio.fixture
    async def finance_agent(self):
        return FinanceAgent()

    async def test_budget_request_approved(self, finance_agent):
        finance_agent._structured_llm = FakeStructuredLLM([
            FinanceDecision(approved=True, reasoning="Sufficient funds available", amount_approved=1000)
        ])
        event = {"type": "budget_request", "amount": 1000, "department": "Marketing"}
        result = await finance_agent.process_event(event)
        assert result["status"] == "approved"
        assert finance_agent.budget_pool == 99000.0

    async def test_budget_request_denied(self, finance_agent):
        finance_agent._structured_llm = FakeStructuredLLM([
            FinanceDecision(approved=False, reasoning="Amount exceeds available budget", amount_approved=0.0)
        ])
        event = {"type": "budget_request", "amount": 500000, "department": "Marketing"}
        result = await finance_agent.process_event(event)
        assert result["status"] == "denied"
        assert finance_agent.budget_pool == 100000.0

    async def test_budget_request_retries_on_bad_output(self, finance_agent):
        good_decision = FinanceDecision(approved=True, reasoning="Approved after retry", amount_approved=200)
        fake = FakeStructuredLLM([ValueError("malformed tool call"), good_decision])
        finance_agent._structured_llm = fake
        event = {"type": "budget_request", "amount": 200, "department": "Operations"}
        result = await finance_agent.process_event(event)
        assert fake.calls == 2
        assert result["reasoning"] == "Approved after retry"

    async def test_budget_request_falls_back_after_exhausting_retries(self, finance_agent):
        fake = FakeStructuredLLM([ValueError("bad json"), ValueError("bad json again")])
        finance_agent._structured_llm = fake
        event = {"type": "budget_request", "amount": 500, "department": "HR"}
        result = await finance_agent.process_event(event)
        assert fake.calls == 2
        assert "llm_fallback" in result["reasoning"]
        assert result["status"] == "approved"


@pytest.mark.asyncio
class TestHRAgent:
    @pytest_asyncio.fixture
    async def hr_agent(self):
        return HRAgent()

    async def test_recruitment_request_approved(self, hr_agent):
        hr_agent._structured_llm = FakeStructuredLLM([
            HRDecision(approved=True, headcount_approved=2, reasoning="Team is stretched thin", morale_impact=0.5)
        ])
        event = {"type": "recruitment_request", "role": "Engineer", "headcount": 2}
        result = await hr_agent.process_event(event)
        assert result["status"] == "approved"
        assert hr_agent.employee_count == 52
        assert hr_agent.team_morale == 8.0

    async def test_recruitment_request_denied(self, hr_agent):
        hr_agent._structured_llm = FakeStructuredLLM([
            HRDecision(approved=False, headcount_approved=0, reasoning="Hiring freeze", morale_impact=-0.2)
        ])
        event = {"type": "recruitment_request", "role": "Engineer", "headcount": 10}
        result = await hr_agent.process_event(event)
        assert result["status"] == "denied"
        assert hr_agent.employee_count == 50

    async def test_recruitment_request_retries_on_bad_output(self, hr_agent):
        good_decision = HRDecision(approved=True, headcount_approved=1, reasoning="Approved after retry")
        fake = FakeStructuredLLM([ValueError("malformed tool call"), good_decision])
        hr_agent._structured_llm = fake
        event = {"type": "recruitment_request", "role": "Designer", "headcount": 1}
        result = await hr_agent.process_event(event)
        assert fake.calls == 2
        assert result["reasoning"] == "Approved after retry"

    async def test_recruitment_request_falls_back_after_exhausting_retries(self, hr_agent):
        fake = FakeStructuredLLM([ValueError("bad json"), ValueError("bad json again")])
        hr_agent._structured_llm = fake
        event = {"type": "recruitment_request", "role": "Sales Rep", "headcount": 2}
        result = await hr_agent.process_event(event)
        assert fake.calls == 2
        assert "llm_fallback" in result["reasoning"]
        assert result["status"] == "approved"

    async def test_morale_is_clamped_to_valid_range(self, hr_agent):
        hr_agent.team_morale = 9.8
        hr_agent._structured_llm = FakeStructuredLLM([
            HRDecision(approved=True, headcount_approved=1, reasoning="Great hire", morale_impact=5.0)
        ])
        await hr_agent.process_event({"type": "recruitment_request", "role": "Engineer", "headcount": 1})
        assert hr_agent.team_morale == 10.0


@pytest.mark.asyncio
class TestOperationsAgent:
    @pytest_asyncio.fixture
    async def operations_agent(self):
        return OperationsAgent()

    async def test_resource_request_approved(self, operations_agent):
        operations_agent._structured_llm = FakeStructuredLLM([
            OperationsDecision(
                approved=True, quantity_approved=500, reasoning="Within pool", efficiency_impact=1.0
            )
        ])
        event = {"type": "resource_request", "resource_type": "Cloud Compute", "quantity": 500}
        result = await operations_agent.process_event(event)
        assert result["status"] == "approved"
        assert operations_agent.resource_pool == 9500
        assert operations_agent.operational_efficiency == 76.0

    async def test_resource_request_denied(self, operations_agent):
        operations_agent._structured_llm = FakeStructuredLLM([
            OperationsDecision(
                approved=False, quantity_approved=0, reasoning="Exceeds pool", efficiency_impact=-1.0
            )
        ])
        event = {"type": "resource_request", "resource_type": "Office Space", "quantity": 50000}
        result = await operations_agent.process_event(event)
        assert result["status"] == "denied"
        assert operations_agent.resource_pool == 10000

    async def test_resource_request_retries_on_bad_output(self, operations_agent):
        good_decision = OperationsDecision(approved=True, quantity_approved=10, reasoning="Approved after retry")
        fake = FakeStructuredLLM([ValueError("malformed tool call"), good_decision])
        operations_agent._structured_llm = fake
        event = {"type": "resource_request", "resource_type": "Equipment", "quantity": 10}
        result = await operations_agent.process_event(event)
        assert fake.calls == 2
        assert result["reasoning"] == "Approved after retry"

    async def test_resource_request_falls_back_after_exhausting_retries(self, operations_agent):
        fake = FakeStructuredLLM([ValueError("bad json"), ValueError("bad json again")])
        operations_agent._structured_llm = fake
        event = {"type": "resource_request", "resource_type": "Cloud Compute", "quantity": 100}
        result = await operations_agent.process_event(event)
        assert fake.calls == 2
        assert "llm_fallback" in result["reasoning"]
        assert result["status"] == "approved"

    async def test_efficiency_is_clamped_to_valid_range(self, operations_agent):
        operations_agent.operational_efficiency = 99.7
        operations_agent._structured_llm = FakeStructuredLLM([
            OperationsDecision(
                approved=True, quantity_approved=1, reasoning="Great allocation", efficiency_impact=5.0
            )
        ])
        await operations_agent.process_event(
            {"type": "resource_request", "resource_type": "Equipment", "quantity": 1}
        )
        assert operations_agent.operational_efficiency == 100.0
