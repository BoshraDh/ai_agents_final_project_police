"""Tests for the deterministic move-replay position tracker."""

from __future__ import annotations

from bb_ai_12_police.domain.belief import BeliefState
from bb_ai_12_police.domain.protocol import Direction, Position

_CONFIG = {"board_and_agents": {"cop_start": [0, 0], "thief_start": [3, 3]}}


def test_from_config_sets_both_starting_positions():
    belief = BeliefState.from_config(_CONFIG, "cop_start", "thief_start")
    assert belief.own_position == Position(0, 0)
    assert belief.opponent_position == Position(3, 3)


def test_apply_own_move_updates_only_own_position():
    belief = BeliefState.from_config(_CONFIG, "cop_start", "thief_start")
    belief.apply_own_move(Direction.SOUTH)
    assert belief.own_position == Position(1, 0)
    assert belief.opponent_position == Position(3, 3)


def test_apply_opponent_move_updates_only_opponent_position():
    belief = BeliefState.from_config(_CONFIG, "cop_start", "thief_start")
    belief.apply_opponent_move(Direction.WEST)
    assert belief.own_position == Position(0, 0)
    assert belief.opponent_position == Position(3, 2)
