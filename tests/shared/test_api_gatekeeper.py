"""Tests for the token-bucket Gatekeeper — deterministic, no real sleeping."""

from __future__ import annotations

import pytest

from bb_ai_12_police.shared.api_gatekeeper import TokenBucketGatekeeper, run_guarded

_CONFIG = {
    "rate_limiter_gatekeeper": {
        "requests_per_minute": 30,
        "concurrent_requests": 2,
        "retry_backoff_sec": 5,
        "max_retries": 3,
        "queue_depth": 100,
    }
}


def test_from_config_reads_all_fields():
    gate = TokenBucketGatekeeper.from_config(_CONFIG)
    assert gate.requests_per_minute == 30
    assert gate.concurrent_requests == 2
    assert gate.retry_backoff_sec == 5
    assert gate.max_retries == 3
    assert gate.queue_depth == 100


def test_try_acquire_succeeds_while_tokens_and_slots_are_available():
    gate = TokenBucketGatekeeper(
        requests_per_minute=60, concurrent_requests=2, retry_backoff_sec=1, max_retries=3,
        queue_depth=10,
    )
    assert gate.try_acquire(now=0.0)
    assert gate.try_acquire(now=0.0)


def test_try_acquire_fails_once_the_concurrency_cap_is_hit():
    gate = TokenBucketGatekeeper(
        requests_per_minute=60, concurrent_requests=1, retry_backoff_sec=1, max_retries=3,
        queue_depth=10,
    )
    assert gate.try_acquire(now=0.0)
    assert not gate.try_acquire(now=0.0)


def test_release_frees_a_concurrency_slot():
    gate = TokenBucketGatekeeper(
        requests_per_minute=60, concurrent_requests=1, retry_backoff_sec=1, max_retries=3,
        queue_depth=10,
    )
    gate.try_acquire(now=0.0)
    gate.release()
    assert gate.try_acquire(now=0.0)


def test_run_guarded_runs_the_action_and_returns_its_result():
    gate = TokenBucketGatekeeper(
        requests_per_minute=60, concurrent_requests=1, retry_backoff_sec=0, max_retries=3,
        queue_depth=10,
    )
    result = run_guarded(gate, lambda: "sent", sleep=lambda _: None)
    assert result == "sent"


def test_run_guarded_retries_then_raises_after_max_retries_when_never_free():
    gate = TokenBucketGatekeeper(
        requests_per_minute=0, concurrent_requests=1, retry_backoff_sec=0, max_retries=2,
        queue_depth=10,
    )
    sleeps = []
    with pytest.raises(RuntimeError):
        run_guarded(gate, lambda: "sent", sleep=sleeps.append)
    assert len(sleeps) == 2  # exactly max_retries backoff sleeps before giving up
