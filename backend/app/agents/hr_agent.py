"""HR Agent Implementation"""
from typing import Any, Dict, Optional, TypedDict

from langgraph.graph import END, StateGraph

from ..core.llm import get_groq_llm
from ..rag import get_decision_memory_store
from .base_agent import BaseAgent
from .schemas import HRDecision

MAX_LLM_ATTEMPTS = 2


class HRGraphState(TypedDict):
    event: Dict[str, Any]
    employee_count: int
    team_morale: float
    attempt: int
    decision: Optional[HRDecision]
    precedent_context: Optional[str]


class HRAgent(BaseAgent):
    """HR Agent for recruitment and team management"""

    def __init__(
        self,
        employee_count: int = 50,
        team_morale: float = 7.5,
        agent_id: Optional[str] = None,
    ):
        super().__init__(
            agent_id=agent_id or "hr_001",
            agent_name="HR Manager",
            description="Manages recruitment, payroll, team performance",
        )
        self.employee_count = employee_count
        self.team_morale = team_morale
        self._structured_llm = get_groq_llm().with_structured_output(HRDecision)
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(HRGraphState)
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

    async def _check_policy(self, state: HRGraphState) -> HRGraphState:
        return state  # passthrough — _route_after_policy does the real work

    def _route_after_policy(self, state: HRGraphState) -> str:
        policy = self.policy
        if policy is None or not policy.enabled:
            return "llm"
        headcount = state["event"].get("headcount", 1)
        if policy.auto_deny_min is not None and headcount >= policy.auto_deny_min:
            return "policy_deny"
        if policy.auto_approve_max is not None and headcount <= policy.auto_approve_max:
            return "policy_approve"
        return "llm"

    async def _policy_approve(self, state: HRGraphState) -> HRGraphState:
        headcount = state["event"].get("headcount", 1)
        decision = HRDecision(
            approved=True,
            headcount_approved=headcount,
            reasoning=f"policy_auto_approved: headcount {headcount} is within the auto-approve threshold",
        )
        return {**state, "decision": decision}

    async def _policy_deny(self, state: HRGraphState) -> HRGraphState:
        headcount = state["event"].get("headcount", 1)
        decision = HRDecision(
            approved=False,
            headcount_approved=0,
            reasoning=f"policy_auto_denied: headcount {headcount} meets or exceeds the auto-deny threshold",
        )
        return {**state, "decision": decision}

    def _route_after_llm(self, state: HRGraphState) -> str:
        if state.get("decision") is not None:
            return "apply"
        if state["attempt"] < MAX_LLM_ATTEMPTS:
            return "retry"
        return "fallback"

    async def _retrieve_memory(self, state: HRGraphState) -> HRGraphState:
        event = state["event"]
        role = event.get("role", "Unspecified Role")
        headcount = event.get("headcount", 1)
        query_text = f"Recruitment request for {headcount} {role}"
        try:
            results = get_decision_memory_store().query_similar(self.agent_id, query_text, k=1)
        except Exception:
            results = []
        precedent_context = results[0]["document"] if results else None
        return {**state, "precedent_context": precedent_context}

    async def _call_llm(self, state: HRGraphState) -> HRGraphState:
        event = state["event"]
        role = event.get("role", "Unspecified Role")
        headcount = event.get("headcount", 1)
        attempt = state.get("attempt", 0) + 1

        prompt = (
            "You are the HR Manager of a startup. Decide whether to approve this "
            "recruitment request.\n"
            f"Current employee count: {state['employee_count']}\n"
            f"Current team morale (0-10): {state['team_morale']:.1f}\n"
            f"Requested role: {role}\n"
            f"Requested headcount: {headcount}\n"
            "Approve the headcount you think is reasonable given team size and morale "
            "(can be less than requested). Give a brief, concrete reasoning, and estimate "
            "the impact on team morale (positive if it relieves overload, negative if budget "
            "concerns loom, small if neutral)."
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

    async def _fallback_decision(self, state: HRGraphState) -> HRGraphState:
        event = state["event"]
        headcount = event.get("headcount", 1)
        approved = headcount <= 5
        decision = HRDecision(
            approved=approved,
            headcount_approved=headcount if approved else 0,
            reasoning="llm_fallback: deterministic rule applied",
            morale_impact=0.1 if approved else -0.1,
        )
        return {**state, "decision": decision}

    async def _apply_decision(self, state: HRGraphState) -> HRGraphState:
        decision: HRDecision = state["decision"]
        if decision.approved:
            self.employee_count += decision.headcount_approved
        if decision.morale_impact:
            self.team_morale = max(0.0, min(10.0, self.team_morale + decision.morale_impact))
        self.decision_count += 1
        return state

    async def _persist_memory(self, state: HRGraphState) -> HRGraphState:
        event = state["event"]
        decision: HRDecision = state["decision"]
        role = event.get("role", "Unspecified Role")
        headcount = event.get("headcount", 1)
        summary_text = (
            f"Recruitment request for {headcount} {role}: "
            f"{'approved' if decision.approved else 'denied'} "
            f"(headcount_approved={decision.headcount_approved}). Reasoning: {decision.reasoning}"
        )
        try:
            get_decision_memory_store().add_decision(
                agent_id=self.agent_id,
                event_type="recruitment_request",
                summary_text=summary_text,
                metadata={
                    "role": role,
                    "headcount": headcount,
                    "approved": decision.approved,
                    "headcount_approved": decision.headcount_approved,
                },
            )
        except Exception:
            pass
        return state

    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = event.get("type")
        if event_type == "recruitment_request":
            return await self.handle_recruitment_request(event)
        return {"status": "unknown_event"}

    async def handle_recruitment_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        initial_state: HRGraphState = {
            "event": event,
            "employee_count": self.employee_count,
            "team_morale": self.team_morale,
            "attempt": 0,
            "decision": None,
            "precedent_context": None,
        }
        final_state = await self._graph.ainvoke(initial_state)
        decision: HRDecision = final_state["decision"]

        return {
            "status": "approved" if decision.approved else "denied",
            "role": event.get("role", "Unspecified Role"),
            "headcount": event.get("headcount", 1),
            "headcount_approved": decision.headcount_approved,
            "reasoning": decision.reasoning,
            "morale_impact": decision.morale_impact,
            "precedent_cited": decision.precedent_cited,
        }

    async def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "employee_count": self.employee_count,
            "team_morale": self.team_morale,
        }
