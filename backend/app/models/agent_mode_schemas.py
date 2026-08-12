"""API-facing agent mode (manual vs auto execution) schemas.

Distinct from AgentPolicyIn (policy_schemas.py): that threshold controls
whether an agent's own approve/deny reasoning short-circuits its LLM call.
This one controls whether the owner must approve a decided action before its
effects apply at all — orthogonal concerns that happen to both be
threshold-shaped, so they're kept as separate collections/routes rather than
merged into one that would conflate "how the agent decides" with "who signs
off before it happens."
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AutoThresholds(BaseModel):
    auto_approve_max: Optional[float] = None


class AgentModeIn(BaseModel):
    mode: str = "manual"  # "manual" | "auto"
    auto_thresholds: AutoThresholds = AutoThresholds()


class AgentModeOut(AgentModeIn):
    updated_at: datetime
