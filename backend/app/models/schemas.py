"""API-facing request/response schemas"""
from typing import Optional

from pydantic import BaseModel


class SimulationStatusOut(BaseModel):
    is_running: bool
    is_paused: bool = False
    tick_count: int
    decision_log_size: int
    run_id: Optional[str] = None
    terminal_status: Optional[str] = None
    error_code: Optional[str] = None
