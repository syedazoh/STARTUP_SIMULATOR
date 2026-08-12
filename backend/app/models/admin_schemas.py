"""API-facing admin schemas.

None of these ever include anything from the `credentials` collection —
admin's view into a business is aggregate operational metadata only. See
routes/admin.py's docstring for why that's a property of what this module
touches, not a permissions check.
"""
from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel


class AdminBusinessSummaryOut(BaseModel):
    id: str
    company_name: str
    industry: str
    owner_email: str
    created_at: datetime
    simulation_status: str  # "never_run" | "running" | "stopped" | "completed"
    task_count: int
    pending_task_count: int


class AdminBusinessDetailOut(BaseModel):
    id: str
    company_name: str
    industry: str
    owner_email: str
    created_at: datetime
    starting_budget: float
    starting_customer_base: int
    starting_headcount: int
    starting_resources: int
    simulation_status: str
    decision_count: int
    task_status_counts: Dict[str, int]


class AdminSystemHealthOut(BaseModel):
    mongo_connected: bool
    business_count: int
    user_count: int
    running_simulation_count: int
