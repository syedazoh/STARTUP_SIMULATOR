"""Autonomous tick loop that feeds synthetic events through the AgentManager"""
import asyncio
import random
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..orchestration.agent_manager import AgentManager
from .config import SimulationConfig
from .event_generator import generate_event

# Every Nth tick, Finance gets a synthetic revenue injection so a long-running
# simulation can't permanently zero out its budget_pool and stall all requests.
REVENUE_TICK_INTERVAL = 5
REVENUE_AMOUNT = 8000.0


def _noop_on_decision(record: Dict[str, Any]) -> None:
    pass


def _noop_on_complete(summary: Any) -> None:
    pass


MAX_RETAINED_RECORDS = 500
DEFAULT_MAX_TICKS = 500
MAX_SERVER_TICKS = 1000
MAX_SERVER_DURATION_SECONDS = 3600.0


class SimulationEngine:
    """Runs ticks against a shared AgentManager without any human clicking each step.

    `on_decision` and `on_complete` are seams for later phases (e.g. persisting each
    tick, and the final run summary, to Mongo) without this class needing to know
    about storage.
    """

    def __init__(
        self,
        agent_manager: AgentManager,
        on_decision: Callable[[Dict[str, Any]], Any] = _noop_on_decision,
        on_complete: Callable[[Any], Any] = _noop_on_complete,
        max_retained_records: int = MAX_RETAINED_RECORDS,
        submit_event: Optional[Callable] = None,
        credit_revenue: Optional[Callable] = None,
    ):
        self.agent_manager = agent_manager
        self.submit_event = submit_event
        self.credit_revenue = credit_revenue
        self.on_decision = on_decision
        self.on_complete = on_complete
        self.max_retained_records = max_retained_records
        self.tick_count = 0
        self.is_running = False
        self.is_paused = False
        self.decision_log: List[Dict[str, Any]] = []
        self._task: Optional[asyncio.Task] = None
        self._resume_event = asyncio.Event()
        self._resume_event.set()

    async def _inject_revenue(self) -> None:
        if self.credit_revenue is not None:
            await self.credit_revenue(REVENUE_AMOUNT, self.tick_count)
            return
        finance = self.agent_manager.agents.get("finance")
        if finance is not None and hasattr(finance, "budget_pool"):
            finance.budget_pool += REVENUE_AMOUNT
            finance.revenue += REVENUE_AMOUNT

    async def _tick(self, event_weights: Optional[Dict[str, float]]) -> None:
        if self.tick_count > 0 and self.tick_count % REVENUE_TICK_INTERVAL == 0:
            await self._inject_revenue()

        agent_statuses = await self.agent_manager.get_all_agents_status()
        event_type, data = generate_event(weights=event_weights, agent_statuses=agent_statuses)
        if self.submit_event is not None:
            await self.submit_event(event_type, data)
        else:
            await self.agent_manager.process_event(event_type, data, source="simulation")

        self.tick_count += 1
        record = {
            "tick": self.tick_count,
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
        self.decision_log.append(record)
        if len(self.decision_log) > self.max_retained_records:
            self.decision_log.pop(0)

        result = self.on_decision(record)
        if asyncio.iscoroutine(result):
            await result

    async def run(self, config: Optional[SimulationConfig] = None) -> None:
        config = config or SimulationConfig()
        max_duration = min(config.duration_seconds, MAX_SERVER_DURATION_SECONDS) if config.duration_seconds else None
        deadline = time.monotonic() + max_duration if max_duration is not None else None
        
        # Enforce a finite tick limit even if requested as unlimited
        if config.ticks is not None:
            effective_ticks = min(config.ticks, MAX_SERVER_TICKS)
        elif deadline is None:
            effective_ticks = DEFAULT_MAX_TICKS
        else:
            effective_ticks = None

        weights = config.resolved_weights()

        self.is_running = True
        try:
            while self.is_running:
                if effective_ticks is not None and self.tick_count >= effective_ticks:
                    break
                if deadline is not None and time.monotonic() >= deadline:
                    break

                await self._resume_event.wait()
                if not self.is_running:
                    break

                await self._tick(weights)

                if self.is_running:
                    interval = random.uniform(config.min_interval, config.max_interval)
                    await asyncio.sleep(interval)
        finally:
            self.is_running = False
            self.is_paused = False
            self._resume_event.set()
            await self._complete()

    async def _complete(self) -> None:
        ceo = self.agent_manager.agents.get("ceo")
        if ceo is None or not hasattr(ceo, "summarize_run"):
            return
        summary = await ceo.summarize_run(self.decision_log)
        result = self.on_complete(summary)
        if asyncio.iscoroutine(result):
            await result

    def start(self, config: Optional[SimulationConfig] = None) -> None:
        if self._task is not None and not self._task.done():
            return
        self._resume_event.set()
        self.is_paused = False
        self._task = asyncio.create_task(self.run(config=config))

    async def stop(self) -> None:
        # Cancel outright rather than relying only on the is_running flag: if the
        # task hasn't started executing yet, run()'s own `self.is_running = True`
        # would otherwise stomp a stop() that raced ahead of it.
        self.is_running = False
        self._resume_event.set()  # unblock a paused loop so it can observe is_running=False and exit
        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None

    def pause(self) -> None:
        if not self.is_running:
            return
        self.is_paused = True
        self._resume_event.clear()

    def resume(self) -> None:
        self.is_paused = False
        self._resume_event.set()

    def status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "tick_count": self.tick_count,
            "decision_log_size": len(self.decision_log),
        }
