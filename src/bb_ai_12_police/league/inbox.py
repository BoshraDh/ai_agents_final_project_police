"""Buffers inbound league-protocol messages so the (separate-thread) MCP
server handlers can hand them off to the main game-loop thread, which
polls for them — the same pattern as `peer/turn_handler.py`'s
`wait_for_own_reveal`, applied to this alternate transport.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class LeagueInbox:
    negotiation: dict[str, Any] | None = None
    _turns: dict[int, dict[str, Any]] = field(default_factory=dict)
    audit: dict[str, Any] | None = None

    def receive_negotiate(self, message: dict[str, Any]) -> None:
        self.negotiation = message

    def receive_turn(self, message: dict[str, Any]) -> None:
        self._turns[message["step"]] = message

    def receive_audit(self, payload: dict[str, Any]) -> None:
        self.audit = payload

    def wait_for_negotiate(self, timeout_sec: float, poll_interval_sec: float = 0.05) -> dict:
        return self._wait(lambda: self.negotiation, timeout_sec, poll_interval_sec, "negotiate")

    def wait_for_turn(
        self, step: int, timeout_sec: float, poll_interval_sec: float = 0.05
    ) -> dict[str, Any]:
        return self._wait(
            lambda: self._turns.get(step), timeout_sec, poll_interval_sec, f"turn {step}"
        )

    def wait_for_audit(self, timeout_sec: float, poll_interval_sec: float = 0.05) -> dict:
        return self._wait(lambda: self.audit, timeout_sec, poll_interval_sec, "audit")

    @staticmethod
    def _wait(
        getter: Callable[[], dict[str, Any] | None],
        timeout_sec: float,
        poll_interval_sec: float,
        what: str,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_sec
        while (value := getter()) is None:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"timed out waiting for opponent's {what}")
            time.sleep(poll_interval_sec)
        return value
