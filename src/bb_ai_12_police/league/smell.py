"""Bridges our `PheromoneField` to the league kit's `smell_grid` wire shape:
`{"r,c": intensity}` string-keyed, not a `Position`-keyed dict.

The kit never discloses an opponent's exact position mid-game — only this
probabilistic scent field — so `guess_position_from_smell` is what feeds
the existing (position-based) `HeuristicBrain` an estimate to chase/evade,
without changing the brain itself.
"""

from __future__ import annotations

from bb_ai_12_police.domain.pheromones import PheromoneField
from bb_ai_12_police.domain.protocol import Position


def serialize_smell_grid(field: PheromoneField) -> dict[str, float]:
    return {f"{pos.row},{pos.col}": round(value, 4) for pos, value in field.as_dict().items()}


def guess_position_from_smell(grid: dict[str, float], fallback: Position) -> Position:
    """The strongest-scented cell, or `fallback` if the grid is empty."""
    if not grid:
        return fallback
    best_key = max(grid, key=grid.__getitem__)
    row_str, col_str = best_key.split(",")
    return Position(row=int(row_str), col=int(col_str))
