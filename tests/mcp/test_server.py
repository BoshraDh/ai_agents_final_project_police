"""Tests for the inbound `receive_move` tool (stage 2 stub logic)."""

from __future__ import annotations

from bb_ai_12_police.mcp.server import receive_move


def test_receive_move_always_replies_stay():
    assert receive_move("N", 1) == {"direction": "STAY", "turn": 1}


def test_receive_move_echoes_the_turn_number():
    assert receive_move("W", 7)["turn"] == 7
