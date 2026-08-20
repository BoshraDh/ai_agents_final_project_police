"""Contract for a pure-algorithm move-decision brain.

Book-binding rule: the move is NEVER chosen by an LLM. Every brain in this
package is deterministic Python; `llm/` (later stages) is restricted to
trash-talk text and an optional bluff-classifier *signal*, never the move
itself.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from bb_ai_12_police.domain.barriers import BarrierSet
from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.protocol import Direction, Position


class BrainBase(ABC):
    """One role's move-decision strategy for a single turn."""

    @abstractmethod
    def decide_move(
        self,
        board: Board,
        barriers: BarrierSet,
        own_position: Position,
        opponent_position: Position,
    ) -> Direction:
        """Return this turn's chosen direction. Must be a legal move."""
