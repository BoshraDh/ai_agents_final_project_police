"""Manhattan-distance heuristic — the shared base for both role brains.

Chooses the legal move that most improves (minimizes, for a pursuer, or
maximizes, for an evader) Manhattan distance to the tracked opponent
position. Zero LLM tokens; ties are broken by `Direction`'s declaration
order so behaviour is reproducible for the replay viewer (stage 7).
"""

from __future__ import annotations

from bb_ai_12_police.domain.barriers import BarrierSet
from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.protocol import Direction, Position
from bb_ai_12_police.domain.rules import legal_moves
from bb_ai_12_police.strategy.base import BrainBase


def manhattan(a: Position, b: Position) -> int:
    return abs(a.row - b.row) + abs(a.col - b.col)


class HeuristicBrain(BrainBase):
    """Subclasses set `_sign`: +1 to pursue (minimize distance), -1 to evade."""

    _sign: int = 1

    def decide_move(
        self,
        board: Board,
        barriers: BarrierSet,
        own_position: Position,
        opponent_position: Position,
    ) -> Direction:
        best_direction = Direction.STAY
        best_score = self._sign * manhattan(own_position, opponent_position)
        for direction in legal_moves(board, barriers, own_position):
            candidate = own_position.moved(direction)
            score = self._sign * manhattan(candidate, opponent_position)
            if score < best_score:
                best_score = score
                best_direction = direction
        return best_direction
