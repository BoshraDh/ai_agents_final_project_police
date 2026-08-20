"""Shared value types used across the domain and runtime layers.

Kept dependency-free (stdlib only) so the domain layer never needs
networking, crypto, or config-loading code to be imported.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    """The two symmetric roles in the game."""

    POLICE = "police"
    THIEF = "thief"


class Direction(StrEnum):
    """Legal single-step moves: 4-orthogonal + STAY (book default move_set)."""

    NORTH = "N"
    SOUTH = "S"
    EAST = "E"
    WEST = "W"
    STAY = "STAY"


#: (row, col) delta applied by each direction. STAY has a zero delta.
DIRECTION_DELTAS: dict[Direction, tuple[int, int]] = {
    Direction.NORTH: (-1, 0),
    Direction.SOUTH: (1, 0),
    Direction.EAST: (0, 1),
    Direction.WEST: (0, -1),
    Direction.STAY: (0, 0),
}


@dataclass(frozen=True, slots=True)
class Position:
    """A cell on the grid. `row`/`col` are 0-indexed from the top-left corner."""

    row: int
    col: int

    def moved(self, direction: Direction) -> Position:
        dr, dc = DIRECTION_DELTAS[direction]
        return Position(self.row + dr, self.col + dc)

    def as_tuple(self) -> tuple[int, int]:
        return (self.row, self.col)


class GameOutcome(StrEnum):
    """Terminal states a sub-game can end in (book Table 2)."""

    ONGOING = "ongoing"
    CAPTURED = "captured"  # cop wins: legal capture_claim confirmed
    SURVIVED = "survived"  # thief wins: reached survival_threshold uncaught
    TECHNICAL_LOSS = "technical_loss"  # timeout / desync / crypto tamper
    TIE = "tie"  # series-level only; not reachable within one sub-game


@dataclass(frozen=True, slots=True)
class MoveAction:
    """One agent's chosen action for a turn."""

    direction: Direction
    place_barrier_at: Position | None = None
