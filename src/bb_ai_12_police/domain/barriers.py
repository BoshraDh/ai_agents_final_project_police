"""Police-placed barriers (book ch.3.4): impassable, capped, honestly declared.

Binding rules this module enforces:
  - only the police may place barriers (checked by the caller/rules layer);
  - a barrier must be placed on a cell adjacent (1 step) to the police's own
    current position, or on the police's own current cell;
  - the total placed can never exceed `max_barriers`;
  - placement is irrevocable for the rest of the sub-game (no removal API).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.protocol import Position


@dataclass(slots=True)
class BarrierSet:
    """Mutable record of barriers placed so far in one sub-game."""

    max_barriers: int
    _placed: set[Position] = field(default_factory=set)

    @property
    def count(self) -> int:
        return len(self._placed)

    @property
    def remaining(self) -> int:
        return self.max_barriers - self.count

    def is_blocked(self, pos: Position) -> bool:
        return pos in self._placed

    def can_place(self, at: Position, cop_pos: Position, board: Board) -> bool:
        if self.remaining <= 0:
            return False
        if not board.in_bounds(at):
            return False
        if at in self._placed:
            return False
        adjacent_or_same = at == cop_pos or _manhattan(at, cop_pos) == 1
        return adjacent_or_same

    def place(self, at: Position, cop_pos: Position, board: Board) -> None:
        if not self.can_place(at, cop_pos, board):
            raise ValueError(f"illegal barrier placement at {at} (cop at {cop_pos})")
        self._placed.add(at)

    def as_list(self) -> list[Position]:
        return sorted(self._placed, key=Position.as_tuple)

    @classmethod
    def from_config(cls, config: dict) -> BarrierSet:
        max_barriers = config["movement_and_barriers"]["max_barriers"]
        return cls(max_barriers=max_barriers)


def _manhattan(a: Position, b: Position) -> int:
    return abs(a.row - b.row) + abs(a.col - b.col)
