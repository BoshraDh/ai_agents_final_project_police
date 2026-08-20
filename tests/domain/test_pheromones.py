"""Tests for the digital pheromone / scent-trail field."""

from __future__ import annotations

from bb_ai_12_police.domain.pheromones import PheromoneField
from bb_ai_12_police.domain.protocol import Position

_CONFIG = {
    "pheromones": {
        "pheromone_center_intensity": 0.9,
        "pheromone_decay": 0.10,
        "pheromone_grid_size": 5,
    }
}


def test_from_config_reads_the_pheromones_block():
    field = PheromoneField.from_config(_CONFIG)
    assert field.center_intensity == 0.9
    assert field.decay_rate == 0.10
    assert field.grid_size == 5


def test_step_deposits_center_intensity_at_the_occupied_cell():
    field = PheromoneField(center_intensity=0.9, decay_rate=0.10, grid_size=5)
    field.step(Position(0, 0))
    assert field.intensity_at(Position(0, 0)) == 0.9


def test_step_decays_previously_visited_cells():
    field = PheromoneField(center_intensity=0.9, decay_rate=0.10, grid_size=5)
    field.step(Position(0, 0))
    field.step(Position(0, 1))
    assert field.intensity_at(Position(0, 0)) == 0.9 * 0.9
    assert field.intensity_at(Position(0, 1)) == 0.9


def test_intensity_at_an_unvisited_cell_is_zero():
    field = PheromoneField(center_intensity=0.9, decay_rate=0.10, grid_size=5)
    assert field.intensity_at(Position(6, 6)) == 0.0


def test_strongest_cell_is_none_when_nothing_deposited():
    field = PheromoneField(center_intensity=0.9, decay_rate=0.10, grid_size=5)
    assert field.strongest_cell() is None


def test_strongest_cell_tracks_the_most_recent_deposit():
    field = PheromoneField(center_intensity=0.9, decay_rate=0.10, grid_size=5)
    field.step(Position(0, 0))
    field.step(Position(1, 1))
    assert field.strongest_cell() == Position(1, 1)
