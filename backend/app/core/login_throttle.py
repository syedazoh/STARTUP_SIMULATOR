"""Shared login budget: five attempts per account per five-minute window.

Count all attempts before password verification, including successful logins,
so concurrent requests cannot bypass the budget. MongoDB's atomic increment
and unique _id share the budget across workers. TTL is only for cleanup;
window selection does not depend on when MongoDB deletes expired documents.
Login fails closed when shared persistence (including its indexes) is unavailable.
"""
import hashlib
import logging
import math
import time
from datetime import datetime, timezone

from fastapi import HTTPException, status
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError

from ..database.mongodb import InMemoryDatabase

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 300


async def check_login_attempt(db, email: str) -> None:
    unavailable = HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Login temporarily unavailable. Please try again later.",
    )
    # The simulator's fallback cannot provide a shared, persistent budget.
    if isinstance(db, InMemoryDatabase):
        raise unavailable

    now = time.time()
    window = int(now // WINDOW_SECONDS)
    expires_at = (window + 1) * WINDOW_SECONDS
    account = hashlib.sha256(email.lower().encode("utf-8")).hexdigest()
    attempts = db["login_attempts"]
    try:
        await attempts.create_index("expires_at", expireAfterSeconds=0)
        attempt = await attempts.find_one_and_update(
            {"_id": f"{account}:{window}"},
            {
                "$inc": {"count": 1},
                "$setOnInsert": {
                    "expires_at": datetime.fromtimestamp(expires_at, timezone.utc),
                },
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError:
        # Do not log database errors, which may contain connection credentials.
        logger.error("Login throttle storage unavailable")
        raise unavailable from None

    if attempt["count"] > MAX_ATTEMPTS:
        logger.warning("Login attempt throttled")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": str(max(1, math.ceil(expires_at - now)))},
        )
