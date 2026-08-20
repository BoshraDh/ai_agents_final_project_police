import pytest

from bb_ai_12_police.domain.barriers import BarrierSet
from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.protocol import Position


def test_can_place_adjacent_to_cop():
    board = Board(size=7)
    barriers = BarrierSet(max_barriers=14)
    cop = Position(3, 3)
    assert barriers.can_place(Position(3, 4), cop, board)
    assert barriers.can_place(Position(3, 3), cop, board)  # cop's own cell allowed
    assert not barriers.can_place(Position(5, 5), cop, board)  # too far


def test_place_and_is_blocked():
    board = Board(size=7)
    barriers = BarrierSet(max_barriers=14)
    cop = Position(3, 3)
    barriers.place(Position(3, 4), cop, board)
    assert barriers.is_blocked(Position(3, 4))
    assert barriers.count == 1
    assert barriers.remaining == 13


def test_place_illegal_raises():
    board = Board(size=7)
    barriers = BarrierSet(max_barriers=14)
    cop = Position(3, 3)
    with pytest.raises(ValueError):
        barriers.place(Position(6, 6), cop, board)


def test_cannot_exceed_max_barriers():
    board = Board(size=7)
    barriers = BarrierSet(max_barriers=1)
    cop = Position(3, 3)
    barriers.place(Position(3, 4), cop, board)
    assert not barriers.can_place(Position(3, 3), cop, board)


def test_from_config():
    barriers = BarrierSet.from_config({"movement_and_barriers": {"max_barriers": 14}})
    assert barriers.max_barriers == 14
