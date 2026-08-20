"""Turn/capture/survival legality (book ch.3.4-3.5): the "hard law" layer.

Composes `Board` + `BarrierSet` so callers get one legality check per move,
and centralizes the two win conditions (capture / survival) so the runtime
layer never has to re-derive them.
"""

from __future__ import annotations

from bb_ai_12_police.domain.barriers import BarrierSet
from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.protocol import Direction, GameOutcome, Position


def is_legal_move(board: Board, barriers: BarrierSet, pos: Position, direction: Direction) -> bool:
    """A move is legal iff the target cell is on-board and not barrier-blocked."""
    target = pos.moved(direction)
    if not board.in_bounds(target):
        return False
    if barriers.is_blocked(target):
        return False
    return True


def legal_moves(board: Board, barriers: BarrierSet, pos: Position) -> list[Direction]:
    return [d for d in Direction if is_legal_move(board, barriers, pos, d)]


def resolve_capture_claim(cop_pos: Position, thief_pos: Position) -> bool:
    """A capture_claim is honest/legal only when the cop and thief share a cell.

    The cop must broadcast a `capture_claim` truthfully; the thief must answer
    honestly (book ch.3.5) — any lie is caught later by the commit-reveal audit
    (crypto layer), not by this function. This function only answers the
    ground-truth geometric question.
    """
    return cop_pos == thief_pos


def check_survival(steps_survived: int, survival_threshold: int) -> bool:
    """True once the thief has survived `survival_threshold` steps uncaught."""
    return steps_survived >= survival_threshold


def outcome_after_step(
    cop_pos: Position,
    thief_pos: Position,
    steps_survived: int,
    survival_threshold: int,
) -> GameOutcome:
    """Single source of truth for "is the sub-game over, and how" after a step."""
    if resolve_capture_claim(cop_pos, thief_pos):
        return GameOutcome.CAPTURED
    if check_survival(steps_survived, survival_threshold):
        return GameOutcome.SURVIVED
    return GameOutcome.ONGOING
