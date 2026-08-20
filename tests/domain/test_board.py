import pytest

from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.protocol import Direction, Position


def test_board_rejects_undersized_grid():
    with pytest.raises(ValueError):
        Board(size=5)


def test_in_bounds():
    board = Board(size=7)
    assert board.in_bounds(Position(0, 0))
    assert board.in_bounds(Position(6, 6))
    assert not board.in_bounds(Position(7, 0))
    assert not board.in_bounds(Position(-1, 0))


def test_legal_directions_from_corner_excludes_off_board():
    board = Board(size=7)
    dirs = board.legal_directions(Position(0, 0))
    assert Direction.NORTH not in dirs
    assert Direction.WEST not in dirs
    assert Direction.SOUTH in dirs
    assert Direction.EAST in dirs
    assert Direction.STAY in dirs


def test_legal_directions_from_center_includes_all_five():
    board = Board(size=7)
    dirs = board.legal_directions(Position(3, 3))
    assert set(dirs) == set(Direction)


def test_start_position_from_config():
    board = Board(size=7)
    config = {"board_and_agents": {"cop_start": [0, 0], "thief_start": [3, 3]}}
    assert board.start_position("cop_start", config) == Position(0, 0)
    assert board.start_position("thief_start", config) == Position(3, 3)


def test_start_position_out_of_bounds_raises():
    board = Board(size=7)
    config = {"board_and_agents": {"cop_start": [9, 9]}}
    with pytest.raises(ValueError):
        board.start_position("cop_start", config)
