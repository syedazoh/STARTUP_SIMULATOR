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


class ArbitrationDecision(BaseModel):
    """CEO agent's structured ruling on a cross-department budget conflict"""
    winner: Literal["finance", "marketing", "compromise"] = Field(
        description="Whose position prevails: 'finance' (deny stands), 'marketing' (full request granted), or 'compromise'"
    )
    final_amount: float = Field(description="The final amount to be released to the requesting department")
    rationale: str = Field(description="Brief explanation referencing both departments' stated positions")


class HRDecision(BaseModel):
    """HR agent's structured decision on a recruitment request"""
    approved: bool = Field(description="Whether the recruitment request is approved")
    headcount_approved: int = Field(description="Headcount approved to hire (0 if denied)")
    reasoning: str = Field(description="Brief explanation of the decision")
    morale_impact: Optional[float] = Field(
        default=None, description="Delta to apply to team morale as a result of this decision"
    )


class OperationsDecision(BaseModel):
    """Operations agent's structured decision on a resource request"""
    approved: bool = Field(description="Whether the resource request is approved")
    quantity_approved: int = Field(description="Quantity approved to allocate (0 if denied)")
    reasoning: str = Field(description="Brief explanation of the decision")
    efficiency_impact: Optional[float] = Field(
        default=None, description="Delta to apply to operational efficiency as a result of this decision"
    )


class RunSummary(BaseModel):
    """CEO agent's end-of-run strategic retrospective over a simulation's decision log"""
    headline: str = Field(description="One-sentence takeaway from this simulation run")
    key_decisions: List[str] = Field(description="A few of the most notable decisions made during the run")
    risks: List[str] = Field(description="Risks or concerning patterns observed in the run")
    recommendation: str = Field(description="A concrete strategic recommendation going forward")
