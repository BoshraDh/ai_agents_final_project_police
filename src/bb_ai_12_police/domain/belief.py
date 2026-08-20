"""Deterministic position tracking from honestly-relayed moves.

Pre-crypto (before stage 6's commit-reveal audit) and pre-deception (before
stage 4's scent/hint layer), every move exchanged over `receive_move` is
taken at face value — so each peer can replay the opponent's moves from the
shared, public start positions (`config/game.json`) and always know its
*exact* position, not just a probabilistic estimate. This class is named
`BeliefState` (matching the book's belief-map terminology) because stage 4
turns it genuinely uncertain: once hints may lie and scent trails decay,
`apply_opponent_move` is replaced by a real Bayesian update over noisy
signals. For now it is an exact replay log.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bb_ai_12_police.domain.protocol import Direction, Position


@dataclass(slots=True)
class BeliefState:
    """Tracks both agents' positions across a running sub-game."""

    own_position: Position
    opponent_position: Position

    def apply_own_move(self, direction: Direction) -> None:
        self.own_position = self.own_position.moved(direction)

    def apply_opponent_move(self, direction: Direction) -> None:
        self.opponent_position = self.opponent_position.moved(direction)

    @classmethod
    def from_config(
        cls, config: dict[str, Any], own_role_key: str, opponent_role_key: str
    ) -> BeliefState:
        """`own_role_key`/`opponent_role_key` are "cop_start" or "thief_start"."""
        board_cfg = config["board_and_agents"]
        own_row, own_col = board_cfg[own_role_key]
        opp_row, opp_col = board_cfg[opponent_role_key]
        return cls(
            own_position=Position(row=own_row, col=own_col),
            opponent_position=Position(row=opp_row, col=opp_col),
        )
