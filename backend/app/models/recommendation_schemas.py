"""Owner-controlled recommendation plans; draft-only social content."""
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

class DraftContent(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False,str_strip_whitespace=True)
    platform: Literal['instagram','facebook']='instagram'
    caption_a: str=Field(default='',max_length=2200)
    caption_b: str=Field(default='',max_length=2200)
    selected_caption: Literal['a','b']='a'
    audience: str=Field(default='',max_length=500)
    rationale: str=Field(default='',max_length=2000)
    promotion_budget: float=Field(default=0,ge=0,le=1000000000)

class RecommendationIn(DraftContent):
    request_id: UUID
    agent: Literal['ceo','finance','marketing','hr','operations']

class RecommendationDecision(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    expected_revision: int=Field(strict=True,ge=0)
    decision: Literal['approve','request_changes','reject']
    feedback: str=Field(default='',max_length=2000)

class RecommendationRevision(BaseModel):
    expected_revision: int=Field(strict=True,ge=0)
    draft: DraftContent
