"""API-facing business profile schemas.

The profile is the canonical "everything agents need to know" document for a
business — one per business, structured so it can be injected wholesale into
agent prompts (and, later, re-embedded into that business's RAG collection
whenever it changes).
"""
from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel, Field


class BrandProfile(BaseModel):
    voice_tone: str = ""
    mission_statement: str = ""
    target_audience: str = ""
    competitors: List[str] = Field(default_factory=list)


class ProductProfile(BaseModel):
    description: str = ""
    pricing_model: str = ""
    price_points: List[float] = Field(default_factory=list)


class MarketingProfile(BaseModel):
    active_channels: List[str] = Field(default_factory=list)
    posting_frequency: str = ""
    content_dos: List[str] = Field(default_factory=list)
    content_donts: List[str] = Field(default_factory=list)


class FinanceProfile(BaseModel):
    monthly_budget_cap: float = 0.0
    currency: str = "USD"
    spend_categories: List[str] = Field(default_factory=list)


class OperationsProfile(BaseModel):
    support_hours: str = ""
    escalation_policy: str = ""


class CustomContextNote(BaseModel):
    label: str
    text: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BusinessProfileIn(BaseModel):
    brand: BrandProfile = Field(default_factory=BrandProfile)
    product: ProductProfile = Field(default_factory=ProductProfile)
    marketing: MarketingProfile = Field(default_factory=MarketingProfile)
    finance: FinanceProfile = Field(default_factory=FinanceProfile)
    operations: OperationsProfile = Field(default_factory=OperationsProfile)


class BusinessProfileOut(BusinessProfileIn):
    business_id: str
    custom_context: List[CustomContextNote] = Field(default_factory=list)
    updated_at: datetime


class CustomContextIn(BaseModel):
    label: str = Field(min_length=1)
    text: str = Field(min_length=1)
