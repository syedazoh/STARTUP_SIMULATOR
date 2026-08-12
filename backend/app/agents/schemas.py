"""Structured-output schemas for agent LLM decisions"""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class FinanceDecision(BaseModel):
    """Finance agent's structured decision on a budget request"""
    approved: bool = Field(description="Whether the budget request is approved")
    reasoning: str = Field(description="Brief explanation of the decision")
    amount_approved: float = Field(description="Amount approved (0 if denied)")
    risk_notes: Optional[str] = Field(default=None, description="Any financial risk notes")
    counter_proposal: Optional[float] = Field(
        default=None,
        description="A smaller counter-offer amount if the full request cannot be approved but a partial amount can",
    )
    precedent_cited: Optional[str] = Field(
        default=None,
        description="If a similar past decision was provided as context, name/summarize which one influenced this decision",
    )


class MarketingDecision(BaseModel):
    """Marketing agent's structured decision on how much budget a campaign needs"""
    campaign_name: str = Field(description="Short name for the campaign")
    desired_budget: float = Field(description="Budget Marketing wants to request for this campaign")
    reasoning: str = Field(description="Brief explanation of why this budget is needed")
    expected_impact: Optional[str] = Field(default=None, description="Expected effect on customers/brand")
    precedent_cited: Optional[str] = Field(
        default=None,
        description="If a similar past decision was provided as context, name/summarize which one influenced this decision",
    )


class ArbitrationDecision(BaseModel):
    """CEO agent's structured ruling on a cross-department budget conflict"""
    winner: Literal["finance", "marketing", "compromise"] = Field(
        description="Whose position prevails: 'finance' (deny stands), 'marketing' (full request granted), or 'compromise'"
    )
    final_amount: float = Field(description="The final amount to be released to the requesting department")
    rationale: str = Field(description="Brief explanation referencing both departments' stated positions")
    precedent_cited: Optional[str] = Field(
        default=None,
        description="If a similar past arbitration was provided as context, name/summarize which one influenced this ruling",
    )


class HRDecision(BaseModel):
    """HR agent's structured decision on a recruitment request"""
    approved: bool = Field(description="Whether the recruitment request is approved")
    headcount_approved: int = Field(description="Headcount approved to hire (0 if denied)")
    reasoning: str = Field(description="Brief explanation of the decision")
    morale_impact: Optional[float] = Field(
        default=None, description="Delta to apply to team morale as a result of this decision"
    )
    precedent_cited: Optional[str] = Field(
        default=None,
        description="If a similar past decision was provided as context, name/summarize which one influenced this decision",
    )


class OperationsDecision(BaseModel):
    """Operations agent's structured decision on a resource request"""
    approved: bool = Field(description="Whether the resource request is approved")
    quantity_approved: int = Field(description="Quantity approved to allocate (0 if denied)")
    reasoning: str = Field(description="Brief explanation of the decision")
    efficiency_impact: Optional[float] = Field(
        default=None, description="Delta to apply to operational efficiency as a result of this decision"
    )
    precedent_cited: Optional[str] = Field(
        default=None,
        description="If a similar past decision was provided as context, name/summarize which one influenced this decision",
    )


class ChatReply(BaseModel):
    """An agent's structured reply to an owner chat message (services/chat.py).

    Separate from the API request/response shapes in models/chat_schemas.py
    — this is the literal shape asked of the LLM via with_structured_output.
    The LLM only ever *requests* an action here; services/chat.py is what
    actually calls create_task(), so a chat-originated action goes through
    the exact same manual/auto/threshold pipeline as every other entry
    point instead of a separate "the chatbot did it" code path.
    """
    reply: str = Field(description="A conversational reply to the owner, written in this agent's voice")
    action_requested: bool = Field(
        default=False,
        description="True only if the owner's message asked you to actually take an action, not just answer a question",
    )
    action_type: Optional[str] = Field(
        default=None, description="Which action type is being requested, if action_requested is true"
    )
    action_payload_json: Optional[str] = Field(
        default=None,
        description="A JSON object, encoded as a string, with that action's required fields, if action_requested is true",
    )


class RunSummary(BaseModel):
    """CEO agent's end-of-run strategic retrospective over a simulation's decision log"""
    headline: str = Field(description="One-sentence takeaway from this simulation run")
    key_decisions: List[str] = Field(description="A few of the most notable decisions made during the run")
    risks: List[str] = Field(description="Risks or concerning patterns observed in the run")
    recommendation: str = Field(description="A concrete strategic recommendation going forward")
