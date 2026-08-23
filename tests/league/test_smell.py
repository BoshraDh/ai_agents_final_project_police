"""Tests for the PheromoneField <-> league smell_grid wire bridge."""

from __future__ import annotations

from bb_ai_12_police.domain.pheromones import PheromoneField
from bb_ai_12_police.domain.protocol import Position
from bb_ai_12_police.league.smell import guess_position_from_smell, serialize_smell_grid

_CONFIG = {"pheromones": {
    "pheromone_center_intensity": 0.9, "pheromone_decay": 0.1, "pheromone_grid_size": 5,
}}


def test_serialize_smell_grid_uses_rc_string_keys():
    field = PheromoneField.from_config(_CONFIG)
    field.step(Position(row=2, col=3))
    grid = serialize_smell_grid(field)
    assert grid == {"2,3": 0.9}


def test_guess_position_from_smell_picks_the_strongest_cell():
    grid = {"1,1": 0.2, "2,3": 0.9, "0,0": 0.5}
    assert guess_position_from_smell(grid, fallback=Position(0, 0)) == Position(row=2, col=3)


def test_guess_position_from_smell_falls_back_when_empty():
    assert guess_position_from_smell({}, fallback=Position(4, 4)) == Position(4, 4)
