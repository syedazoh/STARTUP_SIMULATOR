"""Version-one, bounded synthetic launch contracts; identity is server-derived."""
from typing import Literal
from pydantic import Field
from .automation_schemas import Input, Key

Role = Literal['ceo', 'marketing', 'finance', 'hr', 'operations', 'support', 'strategy']
ROLES = ('ceo', 'marketing', 'finance', 'hr', 'operations', 'support', 'strategy')


class LaunchIn(Input):
    idempotency_key: Key
    seed: int = Field(default=17, ge=0, le=2**31-1, strict=True)
    goal: str = Field(default='Launch a sustainable product campaign', min_length=1, max_length=1000)
    campaign_name: str = Field(default='Synthetic product launch', min_length=1, max_length=200)
    requested_budget_minor: int = Field(default=500000, ge=1, le=10**10, strict=True)
    ticket: str = Field(default='What is the product launch return policy?', min_length=1, max_length=1000)
    duration_seconds: int = Field(default=600, ge=10, le=3600, strict=True)


class RoleMessage(Input):
    schema_version: Literal[1] = 1
    event_id: str = Field(pattern=r'^[a-f0-9]{64}$')
    correlation_id: str = Field(pattern=r'^[a-f0-9]{64}$')
    role: Role
    predecessor_id: str | None = None


class Citation(Input):
    document_id: str
    chunk_id: str
    version: int
    title: str
    quote: str = Field(max_length=500)


class RoleResult(Input):
    schema_version: Literal[1] = 1
    role: Role
    mode: Literal['rule_based', 'extractive_fallback', 'abstention']
    summary: str = Field(max_length=3000)
    reasoning: str = Field(max_length=3000)
    artifact: str = Field(default='', max_length=8000)
    recommended_budget_minor: int | None = Field(default=None, ge=0)
    citations: list[Citation] = Field(default_factory=list, max_length=3)
    context_version: int | None = None
    worker_pid: int
    synthetic: Literal[True] = True
