"""Translates this repo's `config/game.json` into the league kit's 14-key
canonical wire form, and builds/verifies the `negotiate` signature.

The kit's handshake compares the two sides' terms dicts with plain `==`
and aborts on any difference — so the wire form must match key-for-key,
even though our own config uses different (more descriptive) names
internally.
"""

from __future__ import annotations

import hashlib
from typing import Any

from bb_ai_12_police.crypto.commit_reveal import canonical_json


def to_wire_terms(shared: dict[str, Any]) -> dict[str, Any]:
    board = shared["board_and_agents"]
    world = shared["world"]
    movement = shared["movement_and_barriers"]
    pheromones = shared["pheromones"]
    return {
        "axis_origin_corner": board["axis_origin_corner"],
        "axis_start_index": board["axis_start_index"],
        "barriers_max": movement["max_barriers"],
        "board_size": board["grid_size"],
        "cop_start": list(board["cop_start"]),
        "decay_per_step": pheromones["pheromone_decay"],
        "emit_intensity": pheromones["pheromone_center_intensity"],
        "hint_max_words": world["hint_max_words"],
        "max_steps": movement["max_moves"],
        "min_center_intensity": 0.5,
        "num_games": shared["network_and_league"]["num_games"],
        "setting": world["map_area"],
        "smell_grid_size": pheromones["pheromone_grid_size"],
        "thief_start": list(board["thief_start"]),
    }


def terms_signature(terms: dict[str, Any], nonce: str) -> str:
    """signature = SHA256(canonical_json(terms) + "|" + nonce) — kit convention."""
    material = f"{canonical_json(terms)}|{nonce}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def verify_signature(terms: dict[str, Any], nonce: str, signature: str) -> bool:
    return terms_signature(terms, nonce) == signature
