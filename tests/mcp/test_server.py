"""Tests for the inbound `receive_move` tool (stage 2/4 stub logic)."""

from __future__ import annotations

from bb_ai_12_police.mcp.server import receive_move


def test_receive_move_always_replies_stay_with_a_hint():
    reply = receive_move("N", 1)
    assert reply["direction"] == "STAY"
    assert reply["turn"] == 1
    assert reply["hint"]


def test_receive_move_echoes_the_turn_number_regardless_of_hint():
    assert receive_move("W", 7, hint="anything")["turn"] == 7
