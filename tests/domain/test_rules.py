from bb_ai_12_police.domain.barriers import BarrierSet
from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.protocol import Direction, GameOutcome, Position
from bb_ai_12_police.domain.rules import (
    check_survival,
    is_legal_move,
    legal_moves,
    outcome_after_step,
    resolve_capture_claim,
)


def test_is_legal_move_blocked_by_barrier():
    board = Board(size=7)
    barriers = BarrierSet(max_barriers=14)
    barriers.place(Position(3, 4), Position(3, 3), board)
    assert not is_legal_move(board, barriers, Position(3, 3), Direction.EAST)
    assert is_legal_move(board, barriers, Position(3, 3), Direction.WEST)


def test_is_legal_move_off_board():
    board = Board(size=7)
    barriers = BarrierSet(max_barriers=14)
    assert not is_legal_move(board, barriers, Position(0, 0), Direction.NORTH)


def test_legal_moves_always_includes_stay():
    board = Board(size=7)
    barriers = BarrierSet(max_barriers=14)
    assert Direction.STAY in legal_moves(board, barriers, Position(0, 0))


def test_resolve_capture_claim():
    assert resolve_capture_claim(Position(3, 3), Position(3, 3))
    assert not resolve_capture_claim(Position(3, 3), Position(3, 4))


def test_check_survival():
    assert not check_survival(34, 35)
    assert check_survival(35, 35)
    assert check_survival(36, 35)


def test_outcome_after_step_captured_wins_over_survival():
    outcome = outcome_after_step(
        Position(3, 3), Position(3, 3), steps_survived=35, survival_threshold=35
    )
    assert outcome == GameOutcome.CAPTURED


def test_outcome_after_step_survived():
    outcome = outcome_after_step(
        Position(0, 0), Position(3, 3), steps_survived=35, survival_threshold=35
    )
    assert outcome == GameOutcome.SURVIVED


def test_outcome_after_step_ongoing():
    outcome = outcome_after_step(
        Position(0, 0), Position(3, 3), steps_survived=1, survival_threshold=35
    )
    assert outcome == GameOutcome.ONGOING
