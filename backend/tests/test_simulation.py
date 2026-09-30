"""Test Simulation Mode (Phase 5), end-of-run summary (Phase 7), and polish (Phase 8)"""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.agents.schemas import FinanceDecision, HRDecision, MarketingDecision, OperationsDecision, RunSummary
from app.orchestration.agent_manager import AgentManager
from app.simulation import SimulationConfig, SimulationEngine
from app.simulation.config import MAX_SIMULATION_TICKS, MIN_SIMULATION_INTERVAL
from app.simulation.simulation_engine import REVENUE_AMOUNT


class FakeStructuredLLM:
    """Always returns the same canned decision, for deterministic simulation tests"""
    def __init__(self, response):
        self.response = response

    async def ainvoke(self, prompt):
        return self.response


async def _wait_until(condition, timeout: float = 3.0, interval: float = 0.02) -> None:
    """Poll `condition` until it's truthy or `timeout` elapses, instead of a single
    fixed-duration sleep — robust to slow/loaded test environments."""
    elapsed = 0.0
    while not condition():
        if elapsed >= timeout:
            raise AssertionError(f"condition not met within {timeout}s")
        await asyncio.sleep(interval)
        elapsed += interval


async def _wait_for_stable(get_value, stable_window: float = 1.0, poll_interval: float = 0.05, timeout: float = 10.0):
    """Poll `get_value()` until it stops changing for `stable_window` seconds.

    Used instead of asserting a fixed number of in-flight ticks after pause():
    how many ticks are already past the resume-gate check when pause() is called
    isn't a bounded/deterministic count in wall-clock terms — asyncio guarantees
    at most one tick can be "already past the gate" when pause() runs, but under
    heavy process load (e.g. running the full test suite) that single pending
    tick's resumption callback can take well over a second of real time to
    actually get scheduled. `stable_window` has to outlast that delay or this
    falsely concludes "stable" before the last in-flight tick lands.
    """
    elapsed = 0.0
    last = get_value()
    stable_for = 0.0
    while elapsed < timeout:
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
        current = get_value()
        if current == last:
            stable_for += poll_interval
            if stable_for >= stable_window:
                return current
        else:
            stable_for = 0.0
            last = current
    raise AssertionError(f"value did not stabilize within {timeout}s (last={last})")


class FakeMemoryStore:
    """Stands in for DecisionMemoryStore — real embeddings are CPU-bound enough to
    make timing-sensitive tests (pause/duration) flaky, and would otherwise write
    synthetic test data into the real chroma_data directory."""
    def query_similar(self, agent_id, query_text, k=3):
        return []

    def add_decision(self, **kwargs):
        pass


def _build_manager_with_fakes(monkeypatch) -> AgentManager:
    # Every agent now writes to the shared DecisionMemoryStore (Phase 7's RAG
    # generalization), not just Finance — fake it out per-module for all five
    # so simulation tests stay fast and don't write synthetic data into the
    # real chroma_data directory.
    for module in (
        "app.agents.finance_agent",
        "app.agents.marketing_agent",
        "app.agents.hr_agent",
        "app.agents.operations_agent",
        "app.agents.ceo_agent",
    ):
        monkeypatch.setattr(f"{module}.get_decision_memory_store", lambda: FakeMemoryStore())
    mgr = AgentManager()
    # Finance always approves so campaigns never escalate to a real (unmocked) CEO LLM call.
    mgr.agents["finance"]._structured_llm = FakeStructuredLLM(
        FinanceDecision(approved=True, reasoning="Simulated approval", amount_approved=100.0)
    )
    mgr.agents["marketing"]._structured_llm = FakeStructuredLLM(
        MarketingDecision(campaign_name="Sim Campaign", desired_budget=100.0, reasoning="Simulated ask")
    )
    mgr.agents["hr"]._structured_llm = FakeStructuredLLM(
        HRDecision(approved=True, headcount_approved=1, reasoning="Simulated hire")
    )
    mgr.agents["operations"]._structured_llm = FakeStructuredLLM(
        OperationsDecision(approved=True, quantity_approved=1, reasoning="Simulated allocation")
    )
    mgr.agents["ceo"]._summary_llm = FakeStructuredLLM(
        RunSummary(
            headline="Simulated run summary",
            key_decisions=["Approved a campaign"],
            risks=[],
            recommendation="Keep simulating",
        )
    )
    return mgr


@pytest.mark.asyncio
class TestSimulationEngine:
    async def test_run_produces_expected_number_of_ticks(self, monkeypatch):
        engine = SimulationEngine(_build_manager_with_fakes(monkeypatch))
        await engine.run(SimulationConfig(ticks=10, min_interval=0.1, max_interval=0.1))

        assert engine.tick_count == 10
        assert len(engine.decision_log) == 10

    async def test_on_decision_hook_is_called_each_tick(self, monkeypatch):
        received = []
        engine = SimulationEngine(_build_manager_with_fakes(monkeypatch), on_decision=received.append)
        await engine.run(SimulationConfig(ticks=5, min_interval=0.1, max_interval=0.1))

        assert len(received) == 5

    async def test_stop_halts_a_running_simulation(self, monkeypatch):
        engine = SimulationEngine(_build_manager_with_fakes(monkeypatch))
        engine.start(SimulationConfig(ticks=None, min_interval=0.1, max_interval=0.1))
        await engine.stop()

        assert engine.is_running is False

    async def test_on_complete_hook_receives_run_summary(self, monkeypatch):
        received = []
        engine = SimulationEngine(_build_manager_with_fakes(monkeypatch), on_complete=received.append)
        await engine.run(SimulationConfig(ticks=3, min_interval=0.1, max_interval=0.1))

        assert len(received) == 1
        assert received[0].headline == "Simulated run summary"

    async def test_duration_seconds_stops_the_run(self, monkeypatch):
        engine = SimulationEngine(_build_manager_with_fakes(monkeypatch))
        await engine.run(
            SimulationConfig(ticks=None, duration_seconds=0.2, min_interval=0.1, max_interval=0.1)
        )

        assert engine.tick_count > 0
        assert engine.is_running is False

    async def test_revenue_injected_periodically(self, monkeypatch):
        mgr = _build_manager_with_fakes(monkeypatch)
        finance = mgr.agents["finance"]
        starting_revenue = finance.revenue
        starting_budget = finance.budget_pool

        engine = SimulationEngine(mgr)
        # REVENUE_TICK_INTERVAL is 5; six ticks guarantees exactly one injection.
        await engine.run(SimulationConfig(ticks=6, min_interval=0.1, max_interval=0.1))

        assert finance.revenue == starting_revenue + REVENUE_AMOUNT
        assert finance.budget_pool >= starting_budget + REVENUE_AMOUNT - 600  # minus up to 6 approved requests

    async def test_pause_halts_progress_until_resumed(self, monkeypatch):
        # pause() can only stop the *next* tick from starting — any ticks already
        # past the resume-gate check finish regardless, and how many that is isn't
        # a bounded/deterministic count (depends on event-loop scheduling under
        # system load) — so wait for progress to *stabilize* rather than assuming
        # a fixed number of in-flight ticks.
        engine = SimulationEngine(_build_manager_with_fakes(monkeypatch))
        engine.start(SimulationConfig(ticks=None, min_interval=0.1, max_interval=0.1))
        await _wait_until(lambda: engine.tick_count > 0)

        engine.pause()
        assert engine.is_paused is True
        tick_count_settled = await _wait_for_stable(lambda: engine.tick_count)

        await asyncio.sleep(0.5)
        assert engine.tick_count == tick_count_settled

        engine.resume()
        assert engine.is_paused is False
        await _wait_until(lambda: engine.tick_count > tick_count_settled)

        await engine.stop()


class TestSimulationLimits:
    @pytest.mark.parametrize("payload", [
        {"ticks": 0}, {"ticks": -1}, {"ticks": MAX_SIMULATION_TICKS + 1},
        {"min_interval": 0}, {"max_interval": 0},
        {"min_interval": MIN_SIMULATION_INTERVAL / 2},
        {"max_interval": MIN_SIMULATION_INTERVAL / 2},
        {"min_interval": 2, "max_interval": 1},
        {"duration_seconds": 0}, {"duration_seconds": -1},
        *({field: value} for field in ("duration_seconds", "min_interval", "max_interval")
          for value in (float("inf"), float("-inf"), float("nan"))),
    ])
    def test_invalid_work_limits_are_rejected(self, payload):
        with pytest.raises(ValidationError):
            SimulationConfig(**payload)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", [
        {}, {"ticks": None, "duration_seconds": None},
        {"duration_seconds": 3600}, {"ticks": MAX_SIMULATION_TICKS},
    ])
    async def test_server_caps_work_and_retained_records(self, monkeypatch, payload):
        manager = SimpleNamespace(
            agents={}, get_all_agents_status=AsyncMock(return_value={}),
            process_event=AsyncMock(),
        )
        on_decision = AsyncMock()
        engine = SimulationEngine(manager, on_decision=on_decision)
        complete = AsyncMock()
        monkeypatch.setattr(engine, "_complete", complete)
        sleep = AsyncMock()
        monkeypatch.setattr("app.simulation.simulation_engine.asyncio.sleep", sleep)

        await engine.run(SimulationConfig(**payload))

        assert engine.tick_count == MAX_SIMULATION_TICKS
        assert len(engine.decision_log) == MAX_SIMULATION_TICKS
        assert manager.process_event.await_count == MAX_SIMULATION_TICKS
        assert on_decision.await_count == MAX_SIMULATION_TICKS
        assert all(call.args[0] >= MIN_SIMULATION_INTERVAL for call in sleep.await_args_list)
        complete.assert_awaited_once()
        assert not engine.is_running

    @pytest.mark.asyncio
    async def test_resume_after_deadline_does_not_start_another_tick(self, monkeypatch):
        now = 0.0
        manager = SimpleNamespace(agents={}, process_event=AsyncMock())
        engine = SimulationEngine(manager)

        async def resume_after_deadline():
            nonlocal now
            now = 2.0

        monkeypatch.setattr(
            "app.simulation.simulation_engine.time", SimpleNamespace(monotonic=lambda: now)
        )
        monkeypatch.setattr(engine._resume_event, "wait", resume_after_deadline)

        await engine.run(SimulationConfig(duration_seconds=1))

        manager.process_event.assert_not_awaited()
        assert engine.tick_count == 0
