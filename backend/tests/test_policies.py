"""Test agent automation policy engine (Addendum Phase 5)"""
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

import app.database.mongodb as mongodb_module
from app.agents import FinanceAgent, HRAgent, MarketingAgent, OperationsAgent
from app.agents.schemas import FinanceDecision, HRDecision, MarketingDecision, OperationsDecision
from app.main import app
from app.models.policy_schemas import AgentPolicyOut


def _policy(**overrides) -> AgentPolicyOut:
    defaults = dict(enabled=True, auto_approve_max=None, auto_deny_min=None, updated_at=datetime.now(timezone.utc))
    defaults.update(overrides)
    return AgentPolicyOut(**defaults)


class ExplodingLLM:
    """Raises if ever invoked — proves the policy path never reaches the LLM."""
    async def ainvoke(self, prompt):
        raise AssertionError("LLM should not have been called when policy short-circuits")


class FakeStructuredLLM:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    async def ainvoke(self, prompt):
        self.calls += 1
        return self.response


@pytest.mark.asyncio
class TestFinancePolicyShortCircuit:
    @pytest_asyncio.fixture
    async def finance_agent(self):
        return FinanceAgent()

    async def test_auto_approves_under_threshold_without_llm(self, finance_agent):
        finance_agent._structured_llm = ExplodingLLM()
        finance_agent.set_policy(_policy(auto_approve_max=5000))
        result = await finance_agent.process_event(
            {"type": "budget_request", "amount": 1000, "department": "Operations"}
        )
        assert result["status"] == "approved"
        assert "policy_auto_approved" in result["reasoning"]
        assert finance_agent.budget_pool == 99000.0

    async def test_auto_denies_over_threshold_without_llm(self, finance_agent):
        finance_agent._structured_llm = ExplodingLLM()
        finance_agent.set_policy(_policy(auto_deny_min=50000))
        result = await finance_agent.process_event(
            {"type": "budget_request", "amount": 60000, "department": "Operations"}
        )
        assert result["status"] == "denied"
        assert "policy_auto_denied" in result["reasoning"]
        assert finance_agent.budget_pool == 100000.0

    async def test_disabled_policy_falls_through_to_llm(self, finance_agent):
        fake = FakeStructuredLLM(
            FinanceDecision(approved=True, reasoning="Normal LLM path", amount_approved=1000)
        )
        finance_agent._structured_llm = fake
        finance_agent.set_policy(_policy(enabled=False, auto_approve_max=5000))
        result = await finance_agent.process_event(
            {"type": "budget_request", "amount": 1000, "department": "Operations"}
        )
        assert fake.calls == 1
        assert result["reasoning"] == "Normal LLM path"

    async def test_amount_between_thresholds_falls_through_to_llm(self, finance_agent):
        fake = FakeStructuredLLM(
            FinanceDecision(approved=True, reasoning="LLM judgment call", amount_approved=25000)
        )
        finance_agent._structured_llm = fake
        finance_agent.set_policy(_policy(auto_approve_max=5000, auto_deny_min=50000))
        result = await finance_agent.process_event(
            {"type": "budget_request", "amount": 25000, "department": "Operations"}
        )
        assert fake.calls == 1
        assert result["reasoning"] == "LLM judgment call"


@pytest.mark.asyncio
class TestMarketingPolicyShortCircuit:
    @pytest_asyncio.fixture
    async def marketing_agent(self):
        return MarketingAgent()

    async def test_auto_approves_takes_requested_budget_as_is(self, marketing_agent):
        marketing_agent._structured_llm = ExplodingLLM()
        marketing_agent.set_policy(_policy(auto_approve_max=5000))
        result = await marketing_agent.process_event(
            {"type": "campaign_launch", "campaign_name": "Spring Sale", "requested_budget": 2000}
        )
        assert result["desired_budget"] == 2000
        assert "policy_auto_approved" in result["reasoning"]

    async def test_auto_deny_zeroes_the_desired_budget(self, marketing_agent):
        marketing_agent._structured_llm = ExplodingLLM()
        marketing_agent.set_policy(_policy(auto_deny_min=50000))
        result = await marketing_agent.process_event(
            {"type": "campaign_launch", "campaign_name": "Big Splash", "requested_budget": 60000}
        )
        assert result["desired_budget"] == 0
        assert "policy_auto_denied" in result["reasoning"]


@pytest.mark.asyncio
class TestHRPolicyShortCircuit:
    @pytest_asyncio.fixture
    async def hr_agent(self):
        return HRAgent()

    async def test_auto_approves_under_threshold_without_llm(self, hr_agent):
        hr_agent._structured_llm = ExplodingLLM()
        hr_agent.set_policy(_policy(auto_approve_max=3))
        result = await hr_agent.process_event(
            {"type": "recruitment_request", "role": "Engineer", "headcount": 2}
        )
        assert result["status"] == "approved"
        assert result["headcount_approved"] == 2
        assert hr_agent.employee_count == 52

    async def test_auto_denies_over_threshold_without_llm(self, hr_agent):
        hr_agent._structured_llm = ExplodingLLM()
        hr_agent.set_policy(_policy(auto_deny_min=5))
        result = await hr_agent.process_event(
            {"type": "recruitment_request", "role": "Engineer", "headcount": 10}
        )
        assert result["status"] == "denied"
        assert hr_agent.employee_count == 50


@pytest.mark.asyncio
class TestOperationsPolicyShortCircuit:
    @pytest_asyncio.fixture
    async def operations_agent(self):
        return OperationsAgent()

    async def test_auto_approves_under_threshold_without_llm(self, operations_agent):
        operations_agent._structured_llm = ExplodingLLM()
        operations_agent.set_policy(_policy(auto_approve_max=500))
        result = await operations_agent.process_event(
            {"type": "resource_request", "resource_type": "Cloud Compute", "quantity": 200}
        )
        assert result["status"] == "approved"
        assert operations_agent.resource_pool == 9800

    async def test_auto_denies_over_threshold_without_llm(self, operations_agent):
        operations_agent._structured_llm = ExplodingLLM()
        operations_agent.set_policy(_policy(auto_deny_min=5000))
        result = await operations_agent.process_event(
            {"type": "resource_request", "resource_type": "Office Space", "quantity": 9000}
        )
        assert result["status"] == "denied"
        assert operations_agent.resource_pool == 10000


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(mongodb_module, "AsyncIOMotorClient", lambda *a, **kw: AsyncMongoMockClient())
    with TestClient(app) as test_client:
        yield test_client


def _auth_headers(client, email):
    client.post("/api/auth/register", json={"email": email, "password": "supersecret123"})
    login = client.post("/api/auth/login", json={"email": email, "password": "supersecret123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _create_business(client, headers, **overrides):
    payload = {"company_name": "Acme Inc", "industry": "Widgets", **overrides}
    response = client.post("/api/businesses", json=payload, headers=headers)
    return response.json()["id"]


class TestPolicyRoutes:
    def test_get_policy_defaults_to_disabled(self, client):
        headers = _auth_headers(client, "policy1@example.com")
        business_id = _create_business(client, headers)

        response = client.get(f"/api/businesses/{business_id}/agents/finance/policy", headers=headers)
        assert response.status_code == 200
        assert response.json()["enabled"] is False

    def test_put_policy_updates_and_persists(self, client):
        headers = _auth_headers(client, "policy2@example.com")
        business_id = _create_business(client, headers)

        put_response = client.put(
            f"/api/businesses/{business_id}/agents/finance/policy",
            json={"enabled": True, "auto_approve_max": 5000},
            headers=headers,
        )
        assert put_response.status_code == 200
        assert put_response.json()["enabled"] is True
        assert put_response.json()["auto_approve_max"] == 5000

        get_response = client.get(f"/api/businesses/{business_id}/agents/finance/policy", headers=headers)
        assert get_response.json()["auto_approve_max"] == 5000

    def test_ceo_has_no_policy_endpoint(self, client):
        headers = _auth_headers(client, "policy3@example.com")
        business_id = _create_business(client, headers)

        response = client.get(f"/api/businesses/{business_id}/agents/ceo/policy", headers=headers)
        assert response.status_code == 404

    def test_updating_policy_takes_effect_on_live_agent_without_restart(self, client):
        headers = _auth_headers(client, "policy4@example.com")
        business_id = _create_business(client, headers)

        # Touch the agent once so the registry lazily creates it with a real (unmocked)
        # LLM client, proving the policy's short-circuit — not a mock — is what keeps
        # this test network-free: the amount stays under auto_approve_max, so the
        # graph never reaches the call_llm node at all.
        client.get(f"/api/businesses/{business_id}/agents/finance", headers=headers)

        client.put(
            f"/api/businesses/{business_id}/agents/finance/policy",
            json={"enabled": True, "auto_approve_max": 5000},
            headers=headers,
        )

        response = client.post(
            f"/api/businesses/{business_id}/events",
            json={"event_type": "budget_request", "data": {"amount": 1000, "department": "Operations"}},
            headers=headers,
        )
        assert response.status_code == 200

        agent = client.get(f"/api/businesses/{business_id}/agents/finance", headers=headers).json()
        assert agent["budget_pool"] == 99000
