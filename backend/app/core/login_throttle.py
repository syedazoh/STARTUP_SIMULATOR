"""Shared login budget: five attempts per account per five-minute window.

Count all attempts before password verification, including successful logins,
so concurrent requests cannot bypass the budget. MongoDB's atomic increment
and unique _id share the budget across workers. TTL is only for cleanup;
window selection does not depend on when MongoDB deletes expired documents.
Login fails closed when shared persistence (including its indexes) is unavailable.
Local development may explicitly opt into a bounded, process-local budget.
"""
import hashlib
import logging
import math
import time
from datetime import datetime, timezone
from threading import Lock
from weakref import WeakKeyDictionary

from fastapi import HTTPException, status
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError

from ..database.mongodb import InMemoryDatabase
from ..config import settings

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 300
MAX_LOCAL_ACCOUNTS = 4096
_local_budgets = WeakKeyDictionary()
_local_budget_lock = Lock()


def _local_attempt(db, account, now, expires_at, unavailable):
    # Shared by threads within one process; never a production/shared budget.
    # Weak keys release the budget when the temporary database is discarded.
    with _local_budget_lock:
        if db not in _local_budgets:
            _local_budgets[db] = {}
            logger.warning("Development login uses temporary in-memory throttling")
        budget = _local_budgets[db]
        for key in list(budget):
            if budget[key][1] <= now:
                del budget[key]
        if account not in budget and len(budget) >= MAX_LOCAL_ACCOUNTS:
            raise unavailable
        count = budget.get(account, (0, expires_at))[0] + 1
        budget[account] = (count, expires_at)
        return count


async def check_login_attempt(db, email: str) -> None:
    unavailable = HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Login temporarily unavailable. Please try again later.",
    )
    local = isinstance(db, InMemoryDatabase)
    if local and not (settings.debug and settings.allow_in_memory_login):
        raise unavailable

    now = time.time()
    window = int(now // WINDOW_SECONDS)
    expires_at = (window + 1) * WINDOW_SECONDS
    account = hashlib.sha256(email.lower().encode("utf-8")).hexdigest()
    if local:
        count = _local_attempt(db, account, now, expires_at, unavailable)
    else:
        count = await _shared_attempt(db, account, window, expires_at, unavailable)

    if count > MAX_ATTEMPTS:
        logger.warning("Login attempt throttled")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": str(max(1, math.ceil(expires_at - now)))},
        )


async def _shared_attempt(db, account, window, expires_at, unavailable):
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

    return attempt["count"]
