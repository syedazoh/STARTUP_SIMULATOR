"""Finance Agent Implementation"""
import math
from typing import Any, Dict, Optional, TypedDict

from langgraph.graph import END, StateGraph

from ..core.llm import get_groq_llm
from ..rag import get_decision_memory_store
from .base_agent import BaseAgent
from .schemas import FinanceDecision

MAX_LLM_ATTEMPTS = 2
MAX_ARBITRATION_DEPTH = 1


class FinanceGraphState(TypedDict):
    event: Dict[str, Any]
    budget_pool: float
    attempt: int
    decision: Optional[FinanceDecision]
    precedent_context: Optional[str]


class FinanceAgent(BaseAgent):
    """Finance Agent for budgeting and financial analysis"""

    def __init__(self, budget_pool: float = 100000.0, agent_id: Optional[str] = None):
        super().__init__(
            agent_id=agent_id or "finance_001",
            agent_name="Finance Manager",
            description="Manages budgets, forecasts revenue, tracks expenses",
        )
        self.budget_pool = budget_pool
        self.revenue = 0.0
        self.expenses = 0.0
        self._structured_llm = get_groq_llm().with_structured_output(FinanceDecision)
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(FinanceGraphState)
        graph.add_node("check_policy", self._check_policy)
        graph.add_node("policy_approve", self._policy_approve)
        graph.add_node("policy_deny", self._policy_deny)
        graph.add_node("retrieve_memory", self._retrieve_memory)
        graph.add_node("call_llm", self._call_llm)
        graph.add_node("fallback_decision", self._fallback_decision)
        graph.add_node("apply_decision", self._apply_decision)
        graph.add_node("persist_memory", self._persist_memory)

        graph.set_entry_point("check_policy")
        graph.add_conditional_edges(
            "check_policy",
            self._route_after_policy,
            {"policy_approve": "policy_approve", "policy_deny": "policy_deny", "llm": "retrieve_memory"},
        )
        graph.add_edge("policy_approve", "apply_decision")
        graph.add_edge("policy_deny", "apply_decision")
        graph.add_edge("retrieve_memory", "call_llm")
        graph.add_conditional_edges(
            "call_llm",
            self._route_after_llm,
            {"retry": "call_llm", "fallback": "fallback_decision", "apply": "apply_decision"},
        )
        graph.add_edge("fallback_decision", "apply_decision")
        graph.add_edge("apply_decision", "persist_memory")
        graph.add_edge("persist_memory", END)
        return graph.compile()

    async def _check_policy(self, state: FinanceGraphState) -> FinanceGraphState:
        return state  # passthrough — _route_after_policy does the real work

    def _route_after_policy(self, state: FinanceGraphState) -> str:
        policy = self.policy
        if policy is None or not policy.enabled:
            return "llm"
        amount = state["event"].get("amount", 0)
        if policy.auto_deny_min is not None and amount >= policy.auto_deny_min:
            return "policy_deny"
        if policy.auto_approve_max is not None and amount <= policy.auto_approve_max:
            return "policy_approve"
        return "llm"

    async def _policy_approve(self, state: FinanceGraphState) -> FinanceGraphState:
        amount = state["event"].get("amount", 0)
        decision = FinanceDecision(
            approved=True,
            reasoning=f"policy_auto_approved: amount ${amount:.2f} is within the auto-approve threshold",
            amount_approved=amount,
        )
        return {**state, "decision": decision}

    async def _policy_deny(self, state: FinanceGraphState) -> FinanceGraphState:
        amount = state["event"].get("amount", 0)
        decision = FinanceDecision(
            approved=False,
            reasoning=f"policy_auto_denied: amount ${amount:.2f} meets or exceeds the auto-deny threshold",
            amount_approved=0.0,
        )
        return {**state, "decision": decision}

    def _route_after_llm(self, state: FinanceGraphState) -> str:
        if state.get("decision") is not None:
            return "apply"
        if state["attempt"] < MAX_LLM_ATTEMPTS:
            return "retry"
        return "fallback"

    async def _retrieve_memory(self, state: FinanceGraphState) -> FinanceGraphState:
        event = state["event"]
        department = event.get("department", "Unknown")
        amount = event.get("amount", 0)
        query_text = f"Budget request from {department} for ${amount:.2f}"
        try:
            # chromadb's client is synchronous; a local query is fast enough not to
            # warrant a thread-pool hop for this scope.
            results = get_decision_memory_store().query_similar(self.agent_id, query_text, k=1)
        except Exception:
            results = []
        precedent_context = results[0]["document"] if results else None
        return {**state, "precedent_context": precedent_context}

    async def _call_llm(self, state: FinanceGraphState) -> FinanceGraphState:
        event = state["event"]
        amount = event.get("amount", 0)
        department = event.get("department", "Unknown")
        attempt = state.get("attempt", 0) + 1

        prompt = (
            "You are the Finance Manager of a startup. Decide whether to approve this "
            "budget request.\n"
            f"Current available budget pool: ${state['budget_pool']:.2f}\n"
            f"Requesting department: {department}\n"
            f"Requested amount: ${amount:.2f}\n"
            "Approve only if the amount does not exceed the available budget pool. "
            "If you cannot approve the full amount, consider offering a smaller "
            "counter_proposal (e.g. the amount actually available) instead of a flat denial. "
            "Give a brief, concrete reasoning for your decision."
        )
        if state.get("precedent_context"):
            prompt += (
                "\n\nA similar past decision is in memory:\n"
                f"{state['precedent_context']}\n"
                "If it is relevant, factor it into your reasoning and name it in precedent_cited."
            )

        try:
            decision = await self._structured_llm.ainvoke(prompt)
        except Exception:
            decision = None

        return {**state, "attempt": attempt, "decision": decision}

    async def _fallback_decision(self, state: FinanceGraphState) -> FinanceGraphState:
        event = state["event"]
        amount = event.get("amount", 0)
        budget_pool = state["budget_pool"]
        approved = amount <= budget_pool
        decision = FinanceDecision(
            approved=approved,
            reasoning="llm_fallback: deterministic rule applied",
            amount_approved=amount if approved else 0.0,
            counter_proposal=None if approved or budget_pool <= 0 else budget_pool,
        )
        return {**state, "decision": decision}

    async def _apply_decision(self, state: FinanceGraphState) -> FinanceGraphState:
        decision: FinanceDecision = state["decision"]
        if decision is not None and decision.approved:
            event = state.get("event", {})
            requested_amount = float(event.get("amount", 0.0))
            amount_approved = decision.amount_approved

            # Validate amount is finite and non-negative
            if not isinstance(amount_approved, (int, float)) or not math.isfinite(amount_approved) or amount_approved < 0:
                decision.approved = False
                decision.amount_approved = 0.0
                decision.reasoning += " [REJECTED: approved amount must be a finite, non-negative number]"
            # Cannot approve more than was requested
            elif amount_approved > requested_amount:
                decision.approved = False
                decision.amount_approved = 0.0
                decision.reasoning += (
                    f" [REJECTED: approved amount (${amount_approved:.2f}) "
                    f"exceeded requested amount (${requested_amount:.2f})]"
                )
            # Cannot approve more than available budget pool
            elif amount_approved > self.budget_pool:
                decision.approved = False
                decision.amount_approved = 0.0
                decision.reasoning += (
                    f" [REJECTED: approved amount (${amount_approved:.2f}) "
                    f"exceeded available budget pool (${self.budget_pool:.2f})]"
                )
            # Cannot exceed policy denial ceiling if enabled
            elif (
                self.policy is not None
                and self.policy.enabled
                and self.policy.auto_deny_min is not None
                and amount_approved >= self.policy.auto_deny_min
            ):
                decision.approved = False
                decision.amount_approved = 0.0
                decision.reasoning += (
                    f" [REJECTED: approved amount (${amount_approved:.2f}) "
                    f"violates policy auto_deny_min (${self.policy.auto_deny_min:.2f})]"
                )
            else:
                self.budget_pool -= amount_approved

        self.decision_count += 1
        return state

    async def _persist_memory(self, state: FinanceGraphState) -> FinanceGraphState:
        event = state["event"]
        decision: FinanceDecision = state["decision"]
        department = event.get("department", "Unknown")
        amount = event.get("amount", 0)
        summary_text = (
            f"Budget request from {department} for ${amount:.2f}: "
            f"{'approved' if decision.approved else 'denied'} "
            f"(amount_approved=${decision.amount_approved:.2f}). Reasoning: {decision.reasoning}"
        )
        try:
            get_decision_memory_store().add_decision(
                agent_id=self.agent_id,
                event_type="budget_request",
                summary_text=summary_text,
                metadata={
                    "department": department,
                    "amount": amount,
                    "approved": decision.approved,
                    "amount_approved": decision.amount_approved,
                },
            )
        except Exception:
            pass
        return state

    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = event.get("type")
        if event_type == "budget_request":
            return await self.handle_budget_request(event)
        if event_type == "arbitration_result":
            return await self.handle_arbitration_result(event)
        return {"status": "unknown_event"}

    async def handle_budget_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        initial_state: FinanceGraphState = {
            "event": event,
            "budget_pool": self.budget_pool,
            "attempt": 0,
            "decision": None,
            "precedent_context": None,
        }
        final_state = await self._graph.ainvoke(initial_state)
        decision: FinanceDecision = final_state["decision"]

        requested_by = event.get("requested_by")
        depth = event.get("depth", 0)

        if requested_by and self.event_bus is not None:
            await self.event_bus.publish(
                "budget_negotiation",
                {
                    "finance_decision": decision.model_dump(),
                    "original_request": event,
                    "depth": depth,
                },
                source=self.agent_id,
            )
            if (
                not decision.approved
                and event.get("escalate_on_denial")
                and depth < MAX_ARBITRATION_DEPTH
            ):
                await self.event_bus.publish(
                    "arbitration_request",
                    {
                        "finance_position": decision.model_dump(),
                        "marketing_position": {
                            "department": event.get("department", "Unknown"),
                            "campaign_name": event.get("campaign_name"),
                            "requested_amount": event.get("amount", 0),
                            "reasoning": event.get("marketing_reasoning", ""),
                        },
                        "depth": depth,
                    },
                    source=self.agent_id,
                )

        return {
            "status": "approved" if decision.approved else "denied",
            "department": event.get("department", "Unknown"),
            "amount": event.get("amount", 0),
            "amount_approved": decision.amount_approved,
            "reasoning": decision.reasoning,
            "risk_notes": decision.risk_notes,
            "counter_proposal": decision.counter_proposal,
            "precedent_cited": decision.precedent_cited,
        }

    async def handle_arbitration_result(self, event: Dict[str, Any]) -> Dict[str, Any]:
        winner = event.get("winner")
        final_amount = event.get("final_amount", 0) or 0
        # Defence in depth: CEOAgent already clamps final_amount before
        # publishing, but this is the point that actually moves money, so it
        # re-validates rather than trusting an event payload to be well-formed.
        try:
            final_amount = float(final_amount)
        except (TypeError, ValueError):
            final_amount = 0.0
        if not math.isfinite(final_amount) or final_amount <= 0:
            final_amount = 0.0
        elif final_amount > self.budget_pool:
            final_amount = max(self.budget_pool, 0.0)

        if winner != "finance" and final_amount > 0:
            self.budget_pool -= final_amount
        self.decision_count += 1
        return {"status": "arbitration_applied", "winner": winner, "final_amount": final_amount}

    async def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "budget_pool": self.budget_pool,
            "revenue": self.revenue,
            "expenses": self.expenses,
        }
