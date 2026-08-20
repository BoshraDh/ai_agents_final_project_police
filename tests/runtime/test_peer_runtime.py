"""Tests for the turn-loop skeleton (stage 2) — no real networking."""

from __future__ import annotations

from bb_ai_12_police.domain.protocol import Direction
from bb_ai_12_police.runtime.peer_runtime import PeerRuntime


def _runtime() -> PeerRuntime:
    return PeerRuntime(host="127.0.0.1", port=9999, opponent_url="http://unused")


def test_decide_move_is_always_stay():
    assert _runtime()._decide_move(1) is Direction.STAY


def test_run_turn_loop_sends_the_requested_number_of_moves(monkeypatch):
    runtime = _runtime()
    sent = []
    monkeypatch.setattr(
        runtime.transport,
        "send_move",
        lambda direction, turn: sent.append((direction, turn)) or {},
    )
    runtime.run_turn_loop(3)
    assert sent == [("STAY", 1), ("STAY", 2), ("STAY", 3)]
