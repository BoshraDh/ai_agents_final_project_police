"""Tests for the book's GamePhaseMachine legal-transition table."""

from __future__ import annotations

import pytest

from bb_ai_12_police.runtime.state_machine import GamePhaseMachine


def test_starts_waiting_for_opponent():
    assert GamePhaseMachine().state == "WAITING_FOR_OPPONENT"


def test_full_happy_path_cycles_back_to_waiting():
    machine = GamePhaseMachine()
    assert machine.transition("COMPUTING_MOVE") == "COMPUTING_MOVE"
    assert machine.transition("COMMITTING") == "COMMITTING"
    assert machine.transition("AWAITING_REVEAL") == "AWAITING_REVEAL"
    assert machine.transition("VERIFYING") == "VERIFYING"
    assert machine.transition("WAITING_FOR_OPPONENT") == "WAITING_FOR_OPPONENT"


def test_computing_move_can_fail_to_technical_loss():
    machine = GamePhaseMachine()
    machine.transition("COMPUTING_MOVE")
    assert machine.transition("TECHNICAL_LOSS") == "TECHNICAL_LOSS"


def test_awaiting_reveal_can_fail_to_technical_loss():
    machine = GamePhaseMachine()
    machine.transition("COMPUTING_MOVE")
    machine.transition("COMMITTING")
    machine.transition("AWAITING_REVEAL")
    assert machine.transition("TECHNICAL_LOSS") == "TECHNICAL_LOSS"


def test_technical_loss_is_terminal():
    machine = GamePhaseMachine()
    machine.transition("COMPUTING_MOVE")
    machine.transition("TECHNICAL_LOSS")
    with pytest.raises(ValueError):
        machine.transition("WAITING_FOR_OPPONENT")


def test_illegal_transition_raises_and_leaves_state_unchanged():
    machine = GamePhaseMachine()
    with pytest.raises(ValueError, match="Illegal transition"):
        machine.transition("COMMITTING")
    assert machine.state == "WAITING_FOR_OPPONENT"
