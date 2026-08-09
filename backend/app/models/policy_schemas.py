"""API-facing agent automation policy schema.

One generic shape for every department agent: each handles a request that
carries one dominant scalar (amount/desired_budget/headcount/quantity)
approved or denied against a bound, so a uniform policy shape keeps
CRUD/routes/UI consistent across all four rather than four bespoke ones.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AgentPolicyIn(BaseModel):
    enabled: bool = False
    auto_approve_max: Optional[float] = None
    auto_deny_min: Optional[float] = None


class AgentPolicyOut(AgentPolicyIn):
    updated_at: datetime
