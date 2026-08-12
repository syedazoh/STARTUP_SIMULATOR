"""Security-relevant audit trail: who did what, to what, and when.

Distinct from decision_logs (services/persistence.py), which records
business/simulation decisions for the dashboard's decision feed and replay.
audit_logs exists specifically for "who did what" accountability — task
transitions and credential connect/revoke — and always carries a user_id,
which decision_logs does not.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional


async def record_audit(
    db,
    user_id: str,
    business_id: str,
    action: str,
    target_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    await db["audit_logs"].insert_one({
        "user_id": user_id,
        "business_id": business_id,
        "action": action,
        "target_id": target_id,
        "details": details or {},
        "timestamp": datetime.now(timezone.utc),
    })
