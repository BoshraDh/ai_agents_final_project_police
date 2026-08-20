"""Builds the four mandatory end-of-game JSON artifacts (book's report schema).

Each builder returns a plain dict ready for `json.dump` — `report_writer.py`
handles the actual file naming/writing. Kept as pure functions (no I/O) so
they're trivially unit-testable.
"""

from __future__ import annotations

from typing import Any

from bb_ai_12_police.crypto.commit_reveal import CommitRevealLog
from bb_ai_12_police.crypto.step0 import Step0Declaration
from bb_ai_12_police.domain.protocol import GameOutcome, Role
from bb_ai_12_police.domain.scoring import scores_for_both


def build_declaration(step0: Step0Declaration) -> dict[str, Any]:
    return {"payload": step0.payload, "nonce": step0.nonce, "commitment": step0.commitment}


def build_config(shared_config: dict[str, Any], game_json_sha256: str) -> dict[str, Any]:
    return {"shared_config": shared_config, "shared_config_sha256": game_json_sha256}


def build_log(game_id: str, sub_game_number: int, commit_log: CommitRevealLog) -> dict[str, Any]:
    return {
        "game_id": game_id,
        "sub_game_number": sub_game_number,
        "moves": [
            {"turn": e.turn, "payload": e.payload, "nonce": e.nonce, "commitment": e.commitment}
            for e in commit_log.entries()
        ],
        "audit_passed": commit_log.audit(),
    }


def build_result(
    game_id: str, sub_game_number: int, outcome: GameOutcome, own_role: Role
) -> dict[str, Any]:
    scores = scores_for_both(outcome)
    return {
        "game_id": game_id,
        "sub_game_number": sub_game_number,
        "outcome": outcome.value,
        "scores": {role.value: score for role, score in scores.items()},
        "reported_by": own_role.value,
    }
