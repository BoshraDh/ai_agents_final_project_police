"""Tests for the Manhattan-distance heuristic and its role subclasses."""

from __future__ import annotations

from bb_ai_12_police.domain.barriers import BarrierSet
from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.protocol import Direction, Position
from bb_ai_12_police.strategy.heuristic_brain import HeuristicBrain, manhattan
from bb_ai_12_police.strategy.police_brain import PoliceBrain


def test_manhattan_distance():
    assert manhattan(Position(0, 0), Position(3, 4)) == 7


def test_police_brain_moves_toward_the_thief():
    board = Board(size=7)
    barriers = BarrierSet(max_barriers=14)
    brain = PoliceBrain()
    move = brain.decide_move(board, barriers, Position(0, 0), Position(3, 3))
    assert move in (Direction.SOUTH, Direction.EAST)


def test_police_brain_stays_when_already_adjacent_at_the_closest_point():
    board = Board(size=7)
    barriers = BarrierSet(max_barriers=14)
    brain = PoliceBrain()
    move = brain.decide_move(board, barriers, Position(3, 3), Position(3, 3))
    assert move == Direction.STAY


def test_evader_sign_moves_away_from_the_pursuer():
    class EvaderBrain(HeuristicBrain):
        _sign = -1

    board = Board(size=7)
    barriers = BarrierSet(max_barriers=14)
    brain = EvaderBrain()
    move = brain.decide_move(board, barriers, Position(3, 3), Position(0, 0))
    assert move in (Direction.SOUTH, Direction.EAST)
