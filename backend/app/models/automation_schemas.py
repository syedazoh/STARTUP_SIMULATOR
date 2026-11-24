"""Bounded inputs. Actor and business identity are always derived on the server."""

from datetime import timezone
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, field_validator

Department = Literal["finance", "marketing", "hr", "operations", "ceo", "support", "strategy"]
Key = Annotated[str, Field(min_length=1, max_length=100, pattern=r"^[\w-]+$")]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class JobIn(Input):
    kind: Literal["ceo_plan", "daily_brief"]
    idempotency_key: Key
    goal: str = Field(default="", max_length=2000)


class DeadlineIn(Input):
    due_at: AwareDatetime
    expected_version: int = Field(ge=0, strict=True)
    reason: str = Field(min_length=1, max_length=500, pattern=r"\S")
    reminder_minutes: int = Field(default=60, ge=0, le=10080, strict=True)
    escalation_minutes: int = Field(default=60, ge=1, le=10080, strict=True)

    @field_validator("due_at")
    @classmethod
    def utc(cls, v):
        return v.astimezone(timezone.utc)


class DocumentIn(Input):
    key: Key
    title: str = Field(min_length=1, max_length=200, pattern=r"\S")
    text: str = Field(min_length=1, max_length=262144, pattern=r"\S")
    departments: list[Department] = Field(min_length=1, max_length=7)
    expected_version: int = Field(default=0, ge=0, strict=True)


class SearchIn(Input):
    query: str = Field(min_length=2, max_length=1000, pattern=r"\S")
    department: Department
    limit: int = Field(default=5, ge=1, le=8, strict=True)


class MCPGrantIn(Input):
    departments: list[Department] = Field(min_length=1, max_length=7)
    allow_proposals: bool = Field(default=False, strict=True)
