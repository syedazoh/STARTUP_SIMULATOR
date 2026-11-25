"""API-facing chat schemas (per-agent chatbot, Phase 5)."""
from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field

from .task_schemas import TaskOut


class ChatScreen(BaseModel):
    screen: Literal['agent_workspace','boardroom','dashboard'] = 'agent_workspace'
    chart: Optional[Literal['task_status','agent_workload','finance_history']] = None

class ChatMessageIn(BaseModel):
    content: str = Field(min_length=1,max_length=4000)
    screen_context: Optional[ChatScreen] = None


class ChatMessageOut(BaseModel):
    role: str  # "owner" | "agent"
    content: str
    created_at: datetime
    answer_source: Optional[str] = None
    intent: Optional[str] = None


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
    answer_source: Optional[str] = None
    intent: Optional[str] = None
