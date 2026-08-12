"""API-facing media asset schemas (Phase 4: the requires_asset task path)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AgentReviewOut(BaseModel):
    verdict: Optional[str] = None  # "approved" | "rejected" | "reshoot_requested"
    notes: Optional[str] = None


class MediaAssetOut(BaseModel):
    id: str
    business_id: str
    task_id: str
    uploaded_by: str = "owner"
    media_type: str  # "video" | "image"
    agent_review: AgentReviewOut
    uploaded_at: datetime
