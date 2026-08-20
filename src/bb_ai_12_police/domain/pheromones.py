"""Digital pheromone / scent-trail field (book's scent mechanic).

τij(t+1) = max(0, (1-ρ)·τij(t) + Δτij): each step, every tracked cell's
intensity decays by rate ρ, and the cell an agent currently occupies
receives a fresh deposit of `center_intensity`. Currently a single-cell
deposit per step, not spatially spread across `pheromone_grid_size` — the
book's exact spatial falloff shape (uniform vs. weighted) needs
re-confirming before that's implemented; see `docs/TODO.md`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from bb_ai_12_police.domain.protocol import Position


@dataclass(slots=True)
class PheromoneField:
    """Sparse per-cell scent intensities tracked for one agent's trail."""

    center_intensity: float
    decay_rate: float
    grid_size: int
    _intensities: dict[Position, float] = field(default_factory=dict)

    def step(self, occupied: Position) -> None:
        """Decay every tracked cell, then deposit fresh scent at `occupied`."""
        decayed: dict[Position, float] = {}
        for pos, value in self._intensities.items():
            new_value = max(0.0, (1 - self.decay_rate) * value)
            if new_value > 0:
                decayed[pos] = new_value
        decayed[occupied] = decayed.get(occupied, 0.0) + self.center_intensity
        self._intensities = decayed

    def intensity_at(self, pos: Position) -> float:
        return self._intensities.get(pos, 0.0)

    def strongest_cell(self) -> Position | None:
        if not self._intensities:
            return None
        return max(self._intensities, key=self._intensities.__getitem__)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> PheromoneField:
        pheromones = config["pheromones"]
        return cls(
            center_intensity=pheromones["pheromone_center_intensity"],
            decay_rate=pheromones["pheromone_decay"],
            grid_size=pheromones["pheromone_grid_size"],
        )
