"""Test AgentRegistry's restart-safety: on first touch after a restart, an
agent's live numeric state is seeded from its latest agent_snapshots
document instead of always resetting to the business's onboarding baseline
(Phase 8 addendum)."""
from datetime import datetime, timezone

import pytest
from mongomock_motor import AsyncMongoMockClient

from app.models.business_schemas import BusinessOut
from app.orchestration.registry import AgentRegistry


def _business(**overrides) -> BusinessOut:
    defaults = dict(
        id="biz-1",
        owner_user_id="user-1",
        company_name="Acme Inc",
        industry="Widgets",
        starting_budget=100000.0,
        starting_customer_base=1000,
        starting_headcount=50,
        starting_resources=10000,
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return BusinessOut(**defaults)


@pytest.fixture
def db():
    return AsyncMongoMockClient()["test_db"]


@pytest.mark.asyncio
class TestNoRehydrationSource:
    async def test_without_db_falls_back_to_onboarding_baseline(self):
        registry = AgentRegistry(db=None)
        business = _business()
        runtime = await registry.get_or_create(business)
        assert runtime.agent_manager.agents["finance"].budget_pool == 100000.0

    async def test_with_db_but_no_snapshot_falls_back_to_onboarding_baseline(self, db):
        registry = AgentRegistry(db=db)
        business = _business()
        runtime = await registry.get_or_create(business)
        assert runtime.agent_manager.agents["finance"].budget_pool == 100000.0


@pytest.mark.asyncio
class TestRehydratesFromLatestSnapshot:
    async def test_finance_budget_pool_restored_from_snapshot(self, db):
        business = _business(id="biz-2")
        finance_agent_id = f"finance_{business.id}"

        await db["agent_snapshots"].insert_one({
            "business_id": business.id,
            "agent_id": finance_agent_id,
            "state": {"agent_id": finance_agent_id, "agent_name": "Finance Manager", "budget_pool": 42000.0, "revenue": 500.0},
            "timestamp": datetime.now(timezone.utc),
        })

        registry = AgentRegistry(db=db)
        runtime = await registry.get_or_create(business)
        finance = runtime.agent_manager.agents["finance"]
        assert finance.budget_pool == 42000.0
        assert finance.revenue == 500.0

    async def test_uses_the_most_recent_of_multiple_snapshots(self, db):
        business = _business(id="biz-3")
        finance_agent_id = f"finance_{business.id}"

        await db["agent_snapshots"].insert_one({
            "business_id": business.id,
            "agent_id": finance_agent_id,
            "state": {"budget_pool": 10000.0},
            "timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
        })
        await db["agent_snapshots"].insert_one({
            "business_id": business.id,
            "agent_id": finance_agent_id,
            "state": {"budget_pool": 77777.0},
            "timestamp": datetime(2026, 6, 1, tzinfo=timezone.utc),
        })

        registry = AgentRegistry(db=db)
        runtime = await registry.get_or_create(business)
        assert runtime.agent_manager.agents["finance"].budget_pool == 77777.0

    async def test_only_rehydrates_the_matching_business(self, db):
        other_business_finance_id = "finance_other-biz"
        await db["agent_snapshots"].insert_one({
            "business_id": "other-biz",
            "agent_id": other_business_finance_id,
            "state": {"budget_pool": 999999.0},
            "timestamp": datetime.now(timezone.utc),
        })

        business = _business(id="biz-4")
        registry = AgentRegistry(db=db)
        runtime = await registry.get_or_create(business)
        assert runtime.agent_manager.agents["finance"].budget_pool == 100000.0

    async def test_second_get_or_create_reuses_cached_runtime_without_requerying(self, db):
        business = _business(id="biz-5")
        finance_agent_id = f"finance_{business.id}"
        await db["agent_snapshots"].insert_one({
            "business_id": business.id,
            "agent_id": finance_agent_id,
            "state": {"budget_pool": 55555.0},
            "timestamp": datetime.now(timezone.utc),
        })

        registry = AgentRegistry(db=db)
        first = await registry.get_or_create(business)
        first.agent_manager.agents["finance"].budget_pool = 1234.0

        second = await registry.get_or_create(business)
        assert second is first
        assert second.agent_manager.agents["finance"].budget_pool == 1234.0
