"""Marketing Agent Implementation"""
import math
from typing import Any, Dict, Optional, TypedDict

from langgraph.graph import END, StateGraph

from ..core.llm import get_groq_llm
from ..rag import get_decision_memory_store
from .base_agent import BaseAgent
from .schemas import MarketingDecision

MAX_LLM_ATTEMPTS = 2


class MarketingGraphState(TypedDict):
    event: Dict[str, Any]
    attempt: int
    decision: Optional[MarketingDecision]
    precedent_context: Optional[str]


class MarketingAgent(BaseAgent):
    """Marketing Agent for campaigns and market analysis"""

    def __init__(
        self,
        customer_base: int = 1000,
        brand_value: float = 100.0,
        agent_id: Optional[str] = None,
    ):
        super().__init__(
            agent_id=agent_id or "marketing_001",
            agent_name="Marketing Manager",
            description="Plans campaigns, analyzes markets, engages customers",
        )
        self.customer_base = customer_base
        self.brand_value = brand_value
        self._structured_llm = get_groq_llm().with_structured_output(MarketingDecision)
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(MarketingGraphState)
        graph.add_node("check_policy", self._check_policy)
        graph.add_node("policy_approve", self._policy_approve)
        graph.add_node("policy_deny", self._policy_deny)
        graph.add_node("retrieve_memory", self._retrieve_memory)
        graph.add_node("call_llm", self._call_llm)
        graph.add_node("fallback_decision", self._fallback_decision)
        graph.add_node("finalize", self._finalize)
        graph.add_node("persist_memory", self._persist_memory)

        graph.set_entry_point("check_policy")
        graph.add_conditional_edges(
            "check_policy",
            self._route_after_policy,
            {"policy_approve": "policy_approve", "policy_deny": "policy_deny", "llm": "retrieve_memory"},
        )
        graph.add_edge("policy_approve", "finalize")
        graph.add_edge("policy_deny", "finalize")
        graph.add_edge("retrieve_memory", "call_llm")
        graph.add_conditional_edges(
            "call_llm",
            self._route_after_llm,
            {"retry": "call_llm", "fallback": "fallback_decision", "apply": "finalize"},
        )
        graph.add_edge("fallback_decision", "finalize")
        graph.add_edge("finalize", "persist_memory")
        graph.add_edge("persist_memory", END)
        return graph.compile()

    async def _check_policy(self, state: MarketingGraphState) -> MarketingGraphState:
        return state  # passthrough — _route_after_policy does the real work

    def _route_after_policy(self, state: MarketingGraphState) -> str:
        policy = self.policy
        if policy is None or not policy.enabled:
            return "llm"
        requested_budget = state["event"].get("requested_budget", 5000)
        if policy.auto_deny_min is not None and requested_budget >= policy.auto_deny_min:
            return "policy_deny"
        if policy.auto_approve_max is not None and requested_budget <= policy.auto_approve_max:
            return "policy_approve"
        return "llm"

    async def _policy_approve(self, state: MarketingGraphState) -> MarketingGraphState:
        event = state["event"]
        campaign_name = event.get("campaign_name", "Untitled Campaign")
        requested_budget = event.get("requested_budget", 5000)
        decision = MarketingDecision(
            campaign_name=campaign_name,
            desired_budget=requested_budget,
            reasoning=f"policy_auto_approved: requested budget ${requested_budget:.2f} is within the auto-approve threshold",
        )
        return {**state, "decision": decision}

    async def _policy_deny(self, state: MarketingGraphState) -> MarketingGraphState:
        event = state["event"]
        campaign_name = event.get("campaign_name", "Untitled Campaign")
        requested_budget = event.get("requested_budget", 5000)
        decision = MarketingDecision(
            campaign_name=campaign_name,
            desired_budget=0,
            reasoning=f"policy_auto_denied: requested budget ${requested_budget:.2f} meets or exceeds the auto-deny threshold",
        )
        return {**state, "decision": decision}

    def _route_after_llm(self, state: MarketingGraphState) -> str:
        if state.get("decision") is not None:
            return "apply"
        if state["attempt"] < MAX_LLM_ATTEMPTS:
            return "retry"
        return "fallback"

    async def _retrieve_memory(self, state: MarketingGraphState) -> MarketingGraphState:
        event = state["event"]
        campaign_name = event.get("campaign_name", "Untitled Campaign")
        budget = event.get("requested_budget", 5000)
        query_text = f"Campaign launch: {campaign_name} with suggested budget ${budget:.2f}"
        try:
            results = get_decision_memory_store().query_similar(self.agent_id, query_text, k=1)
        except Exception:
            results = []
        precedent_context = results[0]["document"] if results else None
        return {**state, "precedent_context": precedent_context}

    async def _call_llm(self, state: MarketingGraphState) -> MarketingGraphState:
        event = state["event"]
        campaign_name = event.get("campaign_name", "Untitled Campaign")
        base_budget = event.get("requested_budget", 5000)
        attempt = state.get("attempt", 0) + 1

        prompt = (
            "You are the Marketing Manager of a startup, planning a new campaign.\n"
            f"Campaign: {campaign_name}\n"
            f"Suggested starting budget: ${base_budget:.2f}\n"
            f"Current customer base: {self.customer_base}\n"
            f"Current brand value: {self.brand_value:.2f}\n"
            "Decide the budget you want to request from Finance for this campaign, and "
            "explain the expected impact on customers/brand."
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

    async def _fallback_decision(self, state: MarketingGraphState) -> MarketingGraphState:
        event = state["event"]
        campaign_name = event.get("campaign_name", "Untitled Campaign")
        base_budget = event.get("requested_budget", 5000)
        decision = MarketingDecision(
            campaign_name=campaign_name,
            desired_budget=base_budget,
            reasoning="llm_fallback: deterministic rule applied",
        )
        return {**state, "decision": decision}

    async def _finalize(self, state: MarketingGraphState) -> MarketingGraphState:
        return state

    async def _persist_memory(self, state: MarketingGraphState) -> MarketingGraphState:
        event = state["event"]
        decision: MarketingDecision = state["decision"]
        campaign_name = event.get("campaign_name", "Untitled Campaign")
        summary_text = (
            f"Campaign launch '{campaign_name}': requested budget ${decision.desired_budget:.2f}. "
            f"Reasoning: {decision.reasoning}"
        )
        try:
            get_decision_memory_store().add_decision(
                agent_id=self.agent_id,
                event_type="campaign_launch",
                summary_text=summary_text,
                metadata={
                    "campaign_name": campaign_name,
                    "desired_budget": decision.desired_budget,
                },
            )
        except Exception:
            pass
        return state

    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = event.get("type")
        if event_type == "campaign_launch":
            return await self.handle_campaign_launch(event)
        if event_type == "budget_negotiation":
            return await self.handle_budget_negotiation(event)
        if event_type == "arbitration_result":
            return await self.handle_arbitration_result(event)
        return {"status": "unknown_event"}

    async def handle_campaign_launch(self, event: Dict[str, Any]) -> Dict[str, Any]:
        initial_state: MarketingGraphState = {
            "event": event,
            "attempt": 0,
            "decision": None,
            "precedent_context": None,
        }
        final_state = await self._graph.ainvoke(initial_state)
        decision: MarketingDecision = final_state["decision"]
        self.decision_count += 1

        if self.event_bus is not None:
            await self.event_bus.publish(
                "budget_request",
                {
                    "amount": decision.desired_budget,
                    "department": "Marketing",
                    "requested_by": "marketing",
                    "escalate_on_denial": True,
                    "campaign_name": decision.campaign_name,
                    "marketing_reasoning": decision.reasoning,
                    "depth": 0,
                },
                source=self.agent_id,
            )

        return {
            "status": "budget_requested",
            "campaign_name": decision.campaign_name,
            "desired_budget": decision.desired_budget,
            "reasoning": decision.reasoning,
            "precedent_cited": decision.precedent_cited,
        }

    def _apply_campaign_effects(self, amount: float) -> None:
        if amount <= 0:
            return
        self.customer_base += int(amount / 10)
        self.brand_value += amount / 1000

    async def handle_budget_negotiation(self, event: Dict[str, Any]) -> Dict[str, Any]:
        finance_decision = event.get("finance_decision", {})
        self.decision_count += 1
        if finance_decision.get("approved"):
            amount = finance_decision.get("amount_approved", 0)
            self._apply_campaign_effects(amount)
            return {"status": "campaign_launched", "amount": amount}
        return {"status": "awaiting_arbitration_or_denied"}

    async def handle_arbitration_result(self, event: Dict[str, Any]) -> Dict[str, Any]:
        winner = event.get("winner")
        final_amount = event.get("final_amount", 0) or 0
        self.decision_count += 1
        # Same defence in depth as finance_agent: a non-finite or negative
        # final_amount must not grow customer_base/brand_value.
        try:
            final_amount = float(final_amount)
        except (TypeError, ValueError):
            final_amount = 0.0
        if not math.isfinite(final_amount) or final_amount < 0:
            final_amount = 0.0

        if winner != "finance" and final_amount > 0:
            self._apply_campaign_effects(final_amount)
            return {"status": "campaign_launched_via_arbitration", "amount": final_amount}
        return {"status": "campaign_denied"}

    async def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "customer_base": self.customer_base,
            "brand_value": self.brand_value,
        }
