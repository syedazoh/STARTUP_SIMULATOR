"""In-memory rate limiting.

A single-process, in-memory fixed-window limiter — fine for this app's
current single-instance deployment. Would need a shared store (e.g. Redis)
behind a real load balancer running more than one instance, since each
process would otherwise track its own independent window.
"""
import time
from collections import defaultdict
from typing import Dict, List

from fastapi import Depends, HTTPException, status

from ..api.deps import get_current_user
from ..models.auth_schemas import UserOut


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: Dict[str, List[float]] = defaultdict(list)

    def check(self, key: str) -> None:
        now = time.monotonic()
        window_start = now - self.window_seconds
        hits = self._hits[key]
        while hits and hits[0] < window_start:
            hits.pop(0)
        if len(hits) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded — please slow down.",
            )
        hits.append(now)


def rate_limit_dependency(limiter: RateLimiter):
    """Builds a FastAPI dependency that rate-limits per authenticated user
    against the given RateLimiter instance. Each RateLimiter keeps its own
    hit-tracking dict, so separate limiters (e.g. chat vs. task-creation)
    never share a bucket even for the same user."""
    async def _check(user: UserOut = Depends(get_current_user)) -> None:
        limiter.check(user.id)

    return _check
