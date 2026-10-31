"""API-facing chat schemas (per-agent chatbot, Phase 5)."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from .task_schemas import TaskOut


class ChatMessageIn(BaseModel):
    content: str


class ChatMessageOut(BaseModel):
    role: str  # "owner" | "agent"
    content: str
    created_at: datetime


class ChatThreadOut(BaseModel):
    business_id: str
    agent: str
    messages: List[ChatMessageOut]
    updated_at: datetime


class ChatReplyOut(BaseModel):
    thread: ChatThreadOut
    # Set only when the owner's message resulted in a task being created —
    # same object shape the task queue already renders, so the frontend can
    # reuse existing UI for it rather than a bespoke chat-task widget.
    task: Optional[TaskOut] = None
    ai_error: Optional[str] = None
