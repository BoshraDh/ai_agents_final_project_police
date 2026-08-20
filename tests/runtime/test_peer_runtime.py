"""Tests for the turn-loop (stage 3: real brain, still stage-2 wire) — no real networking."""

from __future__ import annotations

from bb_ai_12_police.domain.barriers import BarrierSet
from bb_ai_12_police.domain.belief import BeliefState
from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.protocol import Direction, Position
from bb_ai_12_police.runtime.peer_runtime import PeerRuntime
from bb_ai_12_police.strategy.police_brain import PoliceBrain


def _runtime() -> PeerRuntime:
    return PeerRuntime(
        host="127.0.0.1",
        port=9999,
        opponent_url="http://unused",
        board=Board(size=7),
        barriers=BarrierSet(max_barriers=14),
        belief=BeliefState(own_position=Position(0, 0), opponent_position=Position(3, 3)),
        brain=PoliceBrain(),
    )


def test_decide_move_uses_the_brain_to_chase_the_tracked_opponent():
    assert _runtime()._decide_move() == Direction.SOUTH


def test_run_turn_loop_sends_the_requested_number_of_moves(monkeypatch):
    runtime = _runtime()
    sent = []

    def fake_send_move(direction: str, turn: int) -> dict[str, str | int]:
        sent.append((direction, turn))
        return {"direction": "STAY", "turn": turn}

    monkeypatch.setattr(runtime.transport, "send_move", fake_send_move)
    runtime.run_turn_loop(3)
    assert [t for _, t in sent] == [1, 2, 3]
    assert runtime.belief.opponent_position == Position(3, 3)
