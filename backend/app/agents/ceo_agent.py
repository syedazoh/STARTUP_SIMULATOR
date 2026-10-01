"""CEO Agent - arbitrates cross-department budget conflicts"""
import math
from typing import Any, Dict, List, Optional

from ..core.llm import get_groq_llm
from ..rag import get_decision_memory_store
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

    def _clamp_arbitration_amount(
        self, decision: ArbitrationDecision, marketing_position: Dict[str, Any]
    ) -> ArbitrationDecision:
        """Bounds the ruling's final_amount before it reaches the subscribers.

        The model is free to answer with any number, and Finance's
        handle_arbitration_result subtracts final_amount straight from
        budget_pool — so an unvalidated value here can drain the pool below
        zero, or (if negative) mint budget out of nothing. Marketing's
        handle_arbitration_result grows customer_base off the same number.
        Mirrors finance_agent._apply_decision's pre-subtract validation: clamp
        to [0, what Marketing actually asked for], and treat "finance wins" as
        a zero-amount denial regardless of what final_amount says.
        """
        try:
            requested = float(marketing_position.get("requested_amount") or 0)
        except (TypeError, ValueError):
            requested = 0.0
        if not math.isfinite(requested) or requested < 0:
            requested = 0.0

        amount = decision.final_amount
        clamped = amount
        if not isinstance(amount, (int, float)) or not math.isfinite(amount):
            clamped = 0.0
        else:
            clamped = min(max(float(amount), 0.0), requested)

        if decision.winner == "finance":
            # A denial releases nothing; an amount here would contradict the ruling.
            clamped = 0.0

        if clamped != amount:
            decision.final_amount = clamped
            decision.rationale += (
                f" [ADJUSTED: arbitration amount ${amount} clamped to "
                f"${clamped:.2f}, within the ${requested:.2f} requested]"
            )
        return decision

    async def handle_arbitration_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        finance_position = event.get("finance_position", {})
        marketing_position = event.get("marketing_position", {})
        depth = event.get("depth", 0)
        campaign_name = marketing_position.get("campaign_name", "unknown")

        query_text = f"Arbitration for campaign '{campaign_name}' requesting ${marketing_position.get('requested_amount', 0):.2f}"
        try:
            memory_results = get_decision_memory_store().query_similar(self.agent_id, query_text, k=1)
        except Exception:
            memory_results = []
        precedent_context = memory_results[0]["document"] if memory_results else None

        prompt = (
            "You are the CEO of a startup, arbitrating a budget disagreement between "
            "the Finance and Marketing departments.\n"
            f"Marketing's position: requested ${marketing_position.get('requested_amount', 0):.2f} "
            f"for campaign '{campaign_name}'. "
            f"Marketing's reasoning: {marketing_position.get('reasoning', 'n/a')}\n"
            f"Finance's position: approved={finance_position.get('approved')}, "
            f"counter_proposal=${(finance_position.get('counter_proposal') or 0):.2f}, "
            f"reasoning: {finance_position.get('reasoning', 'n/a')}\n"
            "Decide who prevails: 'finance' (the denial stands, final_amount=0), "
            "'marketing' (grant the full requested amount), or 'compromise' (grant an amount "
            "between Finance's counter-proposal and Marketing's request). "
            "Reference both positions in your rationale."
        )
        if precedent_context:
            prompt += (
                "\n\nA similar past arbitration is in memory:\n"
                f"{precedent_context}\n"
                "If it is relevant, factor it into your ruling and name it in precedent_cited."
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

        decision = self._clamp_arbitration_amount(decision, marketing_position)

        self.decision_count += 1

        summary_text = (
            f"Arbitration for campaign '{campaign_name}': winner={decision.winner}, "
            f"final_amount=${decision.final_amount:.2f}. Rationale: {decision.rationale}"
        )
        try:
            get_decision_memory_store().add_decision(
                agent_id=self.agent_id,
                event_type="arbitration_request",
                summary_text=summary_text,
                metadata={
                    "campaign_name": campaign_name,
                    "winner": decision.winner,
                    "final_amount": decision.final_amount,
                },
            )
        except Exception:
            pass

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
            "precedent_cited": decision.precedent_cited,
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
