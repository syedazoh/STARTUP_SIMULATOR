"""Operations Agent Implementation"""
from typing import Any, Dict, Optional, TypedDict

from langgraph.graph import END, StateGraph

from ..core.llm import get_groq_llm
from ..rag import get_decision_memory_store
from .base_agent import BaseAgent
from .schemas import OperationsDecision

MAX_LLM_ATTEMPTS = 2


class OperationsGraphState(TypedDict):
    event: Dict[str, Any]
    resource_pool: int
    operational_efficiency: float
    attempt: int
    decision: Optional[OperationsDecision]
    precedent_context: Optional[str]


class OperationsAgent(BaseAgent):
    """Operations Agent for supply chain and resources"""

    def __init__(
        self,
        resource_pool: int = 10000,
        operational_efficiency: float = 75.0,
        agent_id: Optional[str] = None,
    ):
        super().__init__(
            agent_id=agent_id or "operations_001",
            agent_name="Operations Manager",
            description="Manages supply chain, allocates resources, optimizes processes",
        )
        self.resource_pool = resource_pool
        self.operational_efficiency = operational_efficiency
        self._structured_llm = get_groq_llm().with_structured_output(OperationsDecision)
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(OperationsGraphState)
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

    async def _check_policy(self, state: OperationsGraphState) -> OperationsGraphState:
        return state  # passthrough — _route_after_policy does the real work

    def _route_after_policy(self, state: OperationsGraphState) -> str:
        policy = self.policy
        if policy is None or not policy.enabled:
            return "llm"
        quantity = state["event"].get("quantity", 1)
        if policy.auto_deny_min is not None and quantity >= policy.auto_deny_min:
            return "policy_deny"
        if policy.auto_approve_max is not None and quantity <= policy.auto_approve_max:
            return "policy_approve"
        return "llm"

    async def _policy_approve(self, state: OperationsGraphState) -> OperationsGraphState:
        quantity = state["event"].get("quantity", 1)
        decision = OperationsDecision(
            approved=True,
            quantity_approved=quantity,
            reasoning=f"policy_auto_approved: quantity {quantity} is within the auto-approve threshold",
        )
        return {**state, "decision": decision}

    async def _policy_deny(self, state: OperationsGraphState) -> OperationsGraphState:
        quantity = state["event"].get("quantity", 1)
        decision = OperationsDecision(
            approved=False,
            quantity_approved=0,
            reasoning=f"policy_auto_denied: quantity {quantity} meets or exceeds the auto-deny threshold",
        )
        return {**state, "decision": decision}

    def _route_after_llm(self, state: OperationsGraphState) -> str:
        if state.get("decision") is not None:
            return "apply"
        if state["attempt"] < MAX_LLM_ATTEMPTS:
            return "retry"
        return "fallback"

    async def _retrieve_memory(self, state: OperationsGraphState) -> OperationsGraphState:
        event = state["event"]
        resource_type = event.get("resource_type", "Unspecified Resource")
        quantity = event.get("quantity", 1)
        query_text = f"Resource request for {quantity} of {resource_type}"
        try:
            results = get_decision_memory_store().query_similar(self.agent_id, query_text, k=1)
        except Exception:
            results = []
        precedent_context = results[0]["document"] if results else None
        return {**state, "precedent_context": precedent_context}

    async def _call_llm(self, state: OperationsGraphState) -> OperationsGraphState:
        event = state["event"]
        resource_type = event.get("resource_type", "Unspecified Resource")
        quantity = event.get("quantity", 1)
        attempt = state.get("attempt", 0) + 1

        prompt = (
            "You are the Operations Manager of a startup. Decide whether to approve this "
            "resource request.\n"
            f"Current resource pool: {state['resource_pool']}\n"
            f"Current operational efficiency (0-100): {state['operational_efficiency']:.1f}\n"
            f"Requested resource type: {resource_type}\n"
            f"Requested quantity: {quantity}\n"
            "Approve only if the quantity does not exceed the available resource pool. "
            "Give a brief, concrete reasoning, and estimate the impact on operational "
            "efficiency (positive if it relieves a bottleneck, negative if it strains capacity)."
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

    async def _fallback_decision(self, state: OperationsGraphState) -> OperationsGraphState:
        event = state["event"]
        quantity = event.get("quantity", 1)
        resource_pool = state["resource_pool"]
        approved = quantity <= resource_pool
        decision = OperationsDecision(
            approved=approved,
            quantity_approved=quantity if approved else 0,
            reasoning="llm_fallback: deterministic rule applied",
            efficiency_impact=0.5 if approved else -0.5,
        )
        return {**state, "decision": decision}

    async def _apply_decision(self, state: OperationsGraphState) -> OperationsGraphState:
        decision: OperationsDecision = state["decision"]
        decision.quantity_approved = min(max(decision.quantity_approved, 0), max(state["event"].get("quantity", 1), 0), max(self.resource_pool, 0))
        if decision.quantity_approved == 0:
            decision.approved = False
        if decision.approved:
            self.resource_pool -= decision.quantity_approved
        if decision.efficiency_impact:
            self.operational_efficiency = max(
                0.0, min(100.0, self.operational_efficiency + decision.efficiency_impact)
            )
        self.decision_count += 1
        return state

    async def _persist_memory(self, state: OperationsGraphState) -> OperationsGraphState:
        event = state["event"]
        decision: OperationsDecision = state["decision"]
        resource_type = event.get("resource_type", "Unspecified Resource")
        quantity = event.get("quantity", 1)
        summary_text = (
            f"Resource request for {quantity} of {resource_type}: "
            f"{'approved' if decision.approved else 'denied'} "
            f"(quantity_approved={decision.quantity_approved}). Reasoning: {decision.reasoning}"
        )
        try:
            get_decision_memory_store().add_decision(
                agent_id=self.agent_id,
                event_type="resource_request",
                summary_text=summary_text,
                metadata={
                    "resource_type": resource_type,
                    "quantity": quantity,
                    "approved": decision.approved,
                    "quantity_approved": decision.quantity_approved,
                },
            )
        except Exception:
            pass
        return state

    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = event.get("type")
        if event_type == "resource_request":
            return await self.handle_resource_request(event)
        return {"status": "unknown_event"}

    async def handle_resource_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        initial_state: OperationsGraphState = {
            "event": event,
            "resource_pool": self.resource_pool,
            "operational_efficiency": self.operational_efficiency,
            "attempt": 0,
            "decision": None,
            "precedent_context": None,
        }
        final_state = await self._graph.ainvoke(initial_state)
        decision: OperationsDecision = final_state["decision"]

        return {
            "status": "approved" if decision.approved else "denied",
            "resource_type": event.get("resource_type", "Unspecified Resource"),
            "quantity": event.get("quantity", 1),
            "quantity_approved": decision.quantity_approved,
            "reasoning": decision.reasoning,
            "efficiency_impact": decision.efficiency_impact,
            "precedent_cited": decision.precedent_cited,
        }

    async def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "resource_pool": self.resource_pool,
            "operational_efficiency": self.operational_efficiency,
        }
