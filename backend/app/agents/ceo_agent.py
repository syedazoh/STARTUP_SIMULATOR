"""CEO Agent - arbitrates cross-department budget conflicts"""
from typing import Any, Dict, List, Optional

from ..core.llm import get_groq_llm
from .base_agent import BaseAgent
from .schemas import ArbitrationDecision, RunSummary


class CEOAgent(BaseAgent):
    """CEO Agent for arbitrating disputes between department agents"""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(
            agent_id=agent_id or "ceo_001",
            agent_name="CEO",
            description="Arbitrates cross-department conflicts and sets strategic direction",
        )
        self._structured_llm = get_groq_llm().with_structured_output(ArbitrationDecision)
        self._summary_llm = get_groq_llm().with_structured_output(RunSummary)

    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        if event.get("type") == "arbitration_request":
            return await self.handle_arbitration_request(event)
        return {"status": "unknown_event"}

    async def handle_arbitration_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        finance_position = event.get("finance_position", {})
        marketing_position = event.get("marketing_position", {})
        depth = event.get("depth", 0)

        prompt = (
            "You are the CEO of a startup, arbitrating a budget disagreement between "
            "the Finance and Marketing departments.\n"
            f"Marketing's position: requested ${marketing_position.get('requested_amount', 0):.2f} "
            f"for campaign '{marketing_position.get('campaign_name', 'unknown')}'. "
            f"Marketing's reasoning: {marketing_position.get('reasoning', 'n/a')}\n"
            f"Finance's position: approved={finance_position.get('approved')}, "
            f"counter_proposal=${(finance_position.get('counter_proposal') or 0):.2f}, "
            f"reasoning: {finance_position.get('reasoning', 'n/a')}\n"
            "Decide who prevails: 'finance' (the denial stands, final_amount=0), "
            "'marketing' (grant the full requested amount), or 'compromise' (grant an amount "
            "between Finance's counter-proposal and Marketing's request). "
            "Reference both positions in your rationale."
        )

        try:
            decision = await self._structured_llm.ainvoke(prompt)
        except Exception:
            counter = marketing_position.get("requested_amount", 0)
            fallback_amount = finance_position.get("counter_proposal") or 0
            decision = ArbitrationDecision(
                winner="compromise" if fallback_amount else "finance",
                final_amount=fallback_amount,
                rationale="llm_fallback: sided with Finance's counter-proposal (or denial) deterministically",
            )

        self.decision_count += 1

        if self.event_bus is not None:
            await self.event_bus.publish(
                "arbitration_result",
                {
                    "winner": decision.winner,
                    "final_amount": decision.final_amount,
                    "rationale": decision.rationale,
                    "department": marketing_position.get("department", "Marketing"),
                    "campaign_name": marketing_position.get("campaign_name"),
                    "depth": depth + 1,
                },
                source="ceo_agent",
            )

        return {
            "status": "arbitrated",
            "winner": decision.winner,
            "final_amount": decision.final_amount,
            "rationale": decision.rationale,
        }

    async def summarize_run(self, decision_log: List[Dict[str, Any]]) -> RunSummary:
        if not decision_log:
            return RunSummary(
                headline="No activity occurred during this run.",
                key_decisions=[],
                risks=[],
                recommendation="Run a longer simulation to generate meaningful activity.",
            )

        event_counts: Dict[str, int] = {}
        for record in decision_log:
            event_counts[record["event_type"]] = event_counts.get(record["event_type"], 0) + 1

        recent_activity = "\n".join(
            f"- Tick {r['tick']}: {r['event_type']} {r['data']}" for r in decision_log[-30:]
        )
        prompt = (
            "You are the CEO reviewing the decision log from a business simulation run.\n"
            f"Event counts by type: {event_counts}\n"
            f"Recent activity (up to last 30 ticks):\n{recent_activity}\n"
            "Write a strategic retrospective: a one-sentence headline, a few key decisions "
            "worth highlighting, any risks or concerning patterns, and one concrete "
            "recommendation going forward."
        )

        try:
            return await self._summary_llm.ainvoke(prompt)
        except Exception:
            return RunSummary(
                headline=f"Simulation ran {len(decision_log)} ticks across {len(event_counts)} event types.",
                key_decisions=[f"{event_type}: {count} occurrences" for event_type, count in event_counts.items()],
                risks=["llm_fallback: unable to generate a detailed narrative summary"],
                recommendation="Review the full decision log manually for details.",
            )

    async def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "decision_count": self.decision_count,
        }
