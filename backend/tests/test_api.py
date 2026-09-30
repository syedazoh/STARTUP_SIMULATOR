"""Test the FastAPI routes with a mocked Mongo (business-scoped, Addendum Phase 3)"""
import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

import app.database.mongodb as mongodb_module
from app.main import app


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


class TestHealthAndRoot:
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_health_reports_mongo_connected(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["mongo"] == "connected"


class TestAgentRoutes:
    def test_list_agents(self, client):
        headers = _auth_headers(client, "agents1@example.com")
        business_id = _create_business(client, headers)

        response = client.get(f"/api/businesses/{business_id}/agents", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {"finance", "marketing", "hr", "operations", "ceo"}

    def test_get_single_agent_reflects_business_starting_state(self, client):
        headers = _auth_headers(client, "agents2@example.com")
        business_id = _create_business(client, headers, starting_budget=42000)

        response = client.get(f"/api/businesses/{business_id}/agents/finance", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["agent_id"] == f"finance_{business_id}"
        assert body["budget_pool"] == 42000

    def test_get_unknown_agent_404s(self, client):
        headers = _auth_headers(client, "agents3@example.com")
        business_id = _create_business(client, headers)

        response = client.get(f"/api/businesses/{business_id}/agents/does-not-exist", headers=headers)
        assert response.status_code == 404

    def test_agents_route_requires_auth(self, client):
        response = client.get("/api/businesses/some-id/agents")
        assert response.status_code == 401

    def test_agents_route_403s_for_non_owner(self, client):
        owner_headers = _auth_headers(client, "owner@example.com")
        business_id = _create_business(client, owner_headers)

        other_headers = _auth_headers(client, "stranger@example.com")
        response = client.get(f"/api/businesses/{business_id}/agents", headers=other_headers)
        assert response.status_code == 403


class TestBusinessIsolation:
    def test_two_businesses_have_independent_agent_state(self, client):
        headers = _auth_headers(client, "multi@example.com")
        business_a = _create_business(client, headers, company_name="A Co", starting_budget=10000)
        business_b = _create_business(client, headers, company_name="B Co", starting_budget=99999)

        agent_a = client.get(f"/api/businesses/{business_a}/agents/finance", headers=headers).json()
        agent_b = client.get(f"/api/businesses/{business_b}/agents/finance", headers=headers).json()

        assert agent_a["budget_pool"] == 10000
        assert agent_b["budget_pool"] == 99999
        assert agent_a["agent_id"] != agent_b["agent_id"]


class TestEventRoutes:
    def test_list_events_starts_empty(self, client):
        headers = _auth_headers(client, "events1@example.com")
        business_id = _create_business(client, headers)

        response = client.get(f"/api/businesses/{business_id}/events", headers=headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_publish_recruitment_event(self, client):
        headers = _auth_headers(client, "events2@example.com")
        business_id = _create_business(client, headers)

        response = client.post(
            f"/api/businesses/{business_id}/events",
            json={"event_type": "recruitment_request", "data": {"role": "Engineer"}, "source": "test"},
            headers=headers,
        )
        assert response.status_code == 200

        history = client.get(f"/api/businesses/{business_id}/events", headers=headers).json()
        assert len(history) == 1
        assert history[0]["event_type"] == "recruitment_request"


class TestSimulationRoutes:
    def test_status_before_any_run(self, client):
        headers = _auth_headers(client, "sim1@example.com")
        business_id = _create_business(client, headers)

        response = client.get(f"/api/businesses/{business_id}/simulation/status", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["is_running"] is False
        assert body["run_id"] is None

    def test_stop_without_running_simulation_conflicts(self, client):
        headers = _auth_headers(client, "sim2@example.com")
        business_id = _create_business(client, headers)

        response = client.post(f"/api/businesses/{business_id}/simulation/stop", headers=headers)
        assert response.status_code == 409

    def test_run_summary_404s_before_any_run(self, client):
        headers = _auth_headers(client, "sim3@example.com")
        business_id = _create_business(client, headers)

        response = client.get(
            f"/api/businesses/{business_id}/simulation/runs/does-not-exist/summary", headers=headers
        )
        assert response.status_code == 404


class TestSimulationResourceLimits:
    @pytest.mark.parametrize("payload", [
        {"ticks": 1001}, {"ticks": -1},
        {"min_interval": 0, "max_interval": 0},
        {"min_interval": 0.05}, {"max_interval": 0.05},
        {"min_interval": 2, "max_interval": 1},
        {"duration_seconds": "Infinity"}, {"min_interval": "NaN"},
    ])
    def test_invalid_limits_do_not_schedule_work(self, client, monkeypatch, payload):
        from unittest.mock import Mock
        from app.simulation import SimulationEngine

        start = Mock()
        monkeypatch.setattr(SimulationEngine, "start", start)
        headers = _auth_headers(client, "limits@example.com")
        business_id = _create_business(client, headers)
        base = f"/api/businesses/{business_id}/simulation"

        response = client.post(f"{base}/start", json=payload, headers=headers)

        assert response.status_code == 422
        start.assert_not_called()
        assert client.get(f"{base}/simulation-runs", headers=headers).json() == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", [{}, {"ticks": None, "duration_seconds": None}])
    async def test_unspecified_limits_bound_persisted_work(self, monkeypatch, payload):
        from types import SimpleNamespace
        from unittest.mock import AsyncMock
        from app.api.routes.simulation import start_simulation
        from app.agents.schemas import RunSummary
        from app.simulation import SimulationConfig
        from app.simulation.config import MAX_SIMULATION_TICKS

        summary = RunSummary(headline="Done", key_decisions=[], risks=[], recommendation="Stop")
        manager = SimpleNamespace(
            agents={"ceo": SimpleNamespace(summarize_run=AsyncMock(return_value=summary))},
            get_all_agents_status=AsyncMock(return_value={"ceo": {"agent_id": "ceo_test"}}),
            process_event=AsyncMock(),
        )
        runtime = SimpleNamespace(simulation_engine=None, agent_manager=manager)
        db = AsyncMongoMockClient()["simulation_limits"]
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(
            db=db, agent_registry=SimpleNamespace(get_or_create=AsyncMock(return_value=runtime)),
        )))
        monkeypatch.setattr("app.simulation.simulation_engine.asyncio.sleep", AsyncMock())

        result = await start_simulation(SimulationConfig(**payload), request, SimpleNamespace(id="test"))
        await runtime.simulation_engine._task

        run = await db["simulation_runs"].find_one({"run_id": result["run_id"]})
        assert run["status"] == "completed"
        assert run["ended_at"] is not None
        assert run["tick_count"] == MAX_SIMULATION_TICKS
        assert await db["decision_logs"].count_documents({}) == MAX_SIMULATION_TICKS
        assert await db["agent_snapshots"].count_documents({}) == MAX_SIMULATION_TICKS
        assert await db["run_summaries"].count_documents({}) == 1
