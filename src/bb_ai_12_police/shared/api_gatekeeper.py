"""Gatekeeper: token-bucket rate limiter guarding the Gmail send call.

Book's `rate_limiter_gatekeeper` config block (`requests_per_minute`,
`concurrent_requests`, `retry_backoff_sec`, `max_retries`, `queue_depth`).
`TokenBucketGatekeeper` implements the core token-bucket + concurrency-cap
mechanism; `run_guarded` retries with backoff up to `max_retries` when no
slot is free. `queue_depth` is stored/validated but no bounded queue is
built here — a single caller (the email sender) never needs one; revisit
if a real multi-request Gatekeeper use case appears later.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TokenBucketGatekeeper:
    requests_per_minute: int
    concurrent_requests: int
    retry_backoff_sec: float
    max_retries: int
    queue_depth: int
    _tokens: float = field(init=False)
    _last_refill: float | None = field(init=False, default=None)
    _in_flight: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        self._tokens = float(self.requests_per_minute)

    def try_acquire(self, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        if self._last_refill is not None:
            elapsed = now - self._last_refill
            refill_rate = self.requests_per_minute / 60.0
            self._tokens = min(self.requests_per_minute, self._tokens + elapsed * refill_rate)
        self._last_refill = now

        if self._in_flight >= self.concurrent_requests or self._tokens < 1:
            return False
        self._tokens -= 1
        self._in_flight += 1
        return True

    def release(self) -> None:
        self._in_flight = max(0, self._in_flight - 1)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> TokenBucketGatekeeper:
        g = config["rate_limiter_gatekeeper"]
        return cls(
            requests_per_minute=g["requests_per_minute"],
            concurrent_requests=g["concurrent_requests"],
            retry_backoff_sec=g["retry_backoff_sec"],
            max_retries=g["max_retries"],
            queue_depth=g["queue_depth"],
        )


def run_guarded[T](
    gatekeeper: TokenBucketGatekeeper,
    action: Callable[[], T],
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Runs `action` once a gatekeeper slot is free, retrying with backoff."""
    attempts = 0
    while True:
        if gatekeeper.try_acquire():
            try:
                return action()
            finally:
                gatekeeper.release()
        attempts += 1
        if attempts > gatekeeper.max_retries:
            raise RuntimeError("gatekeeper: exceeded max_retries waiting for a rate-limit slot")
        sleep(gatekeeper.retry_backoff_sec)
