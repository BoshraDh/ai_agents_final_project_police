"""The discrete grid arena (book ch.3): bounds, legality, movement.

The board itself never blocks a move because of barriers or the
opponent's position — that cross-cutting legality lives in
`rules.is_legal_move`, which composes `Board` with `BarrierSet`.
This module only knows about the grid's own shape.
"""

from __future__ import annotations

from dataclasses import dataclass

from bb_ai_12_police.domain.protocol import Direction, Position


@dataclass(frozen=True, slots=True)
class Board:
    """A `size` x `size` grid, 0-indexed from the top-left corner (0,0)."""

    size: int

    def __post_init__(self) -> None:
        if self.size < 7:
            raise ValueError(f"grid_size must be >= 7 (book minimum), got {self.size}")

    def in_bounds(self, pos: Position) -> bool:
        return 0 <= pos.row < self.size and 0 <= pos.col < self.size

    def neighbors(self, pos: Position) -> dict[Direction, Position]:
        """All 4-orthogonal + STAY targets from `pos`, without bounds filtering."""
        return {d: pos.moved(d) for d in Direction}

    def legal_directions(self, pos: Position) -> list[Direction]:
        """Directions that stay on the board (ignores barriers/opponent)."""
        return [d for d, target in self.neighbors(pos).items() if self.in_bounds(target)]

    @classmethod
    def from_config(cls, config: dict) -> Board:
        grid_size = config["board_and_agents"]["grid_size"]
        return cls(size=grid_size)

    def start_position(self, role_key: str, config: dict) -> Position:
        """`role_key` is "cop_start" or "thief_start" per the shared game.json schema."""
        row, col = config["board_and_agents"][role_key]
        pos = Position(row=row, col=col)
        if not self.in_bounds(pos):
            raise ValueError(f"{role_key}={pos} is outside a {self.size}x{self.size} board")
        return pos
