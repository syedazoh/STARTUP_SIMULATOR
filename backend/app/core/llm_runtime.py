"""One shared, bounded AI queue for the supported single-process backend."""

import asyncio
import random
import time
from weakref import WeakKeyDictionary

from .llm_errors import (
    LLMBusyError, LLMCallFailed, classify_llm_error, retry_after_seconds,
)

MAX_ATTEMPTS = 2
TOTAL_TIMEOUT_SECONDS = 30
MAX_PENDING_REQUESTS = 16


class RequestGate:
    def __init__(self, min_interval=2.0, *, clock=time.monotonic, sleep=asyncio.sleep):
        self.min_interval = min_interval
        self.clock, self.sleep = clock, sleep
        self.lock = asyncio.Lock()
        self.next_start = 0.0
        self.pending = 0

    async def invoke(self, call):
        if self.pending >= MAX_PENDING_REQUESTS:
            raise LLMCallFailed(LLMBusyError())
        self.pending += 1
        deadline = self.clock() + TOTAL_TIMEOUT_SECONDS
        try:
            return await asyncio.wait_for(self._invoke(call, deadline), TOTAL_TIMEOUT_SECONDS)
        except asyncio.CancelledError:
            raise
        except LLMCallFailed:
            raise
        except Exception as exc:
            raise LLMCallFailed(exc) from None
        finally:
            self.pending -= 1

    async def _invoke(self, call, deadline):
        async with self.lock:
            for attempt in range(MAX_ATTEMPTS):
                delay = max(0.0, self.next_start - self.clock())
                if delay >= deadline - self.clock():
                    raise LLMBusyError(delay)
                if delay:
                    await self.sleep(delay)
                self.next_start = self.clock() + self.min_interval
                try:
                    return await call()
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    category = classify_llm_error(exc).code
                    if category not in {"rate_limit", "connection", "provider_error"}:
                        raise
                    # Never retry earlier than Retry-After. Retain the cooldown
                    # even when this request cannot wait long enough to retry.
                    delay = retry_after_seconds(exc)
                    if delay is None:
                        delay = 2 ** attempt + random.uniform(0, 0.25)
                    self.next_start = max(self.next_start, self.clock() + delay)
                    if attempt + 1 == MAX_ATTEMPTS:
                        raise


# All models/temperatures/businesses share the gate on the server event loop.
# Fresh test event loops get independent locks; multiple workers remain unsupported.
_gates = WeakKeyDictionary()


def request_gate(min_interval):
    loop = asyncio.get_running_loop()
    if loop not in _gates:
        _gates[loop] = RequestGate(min_interval)
    return _gates[loop]
