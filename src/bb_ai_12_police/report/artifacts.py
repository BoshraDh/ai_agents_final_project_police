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


def build_log(
    game_id: str,
    sub_game_number: int,
    commit_log: CommitRevealLog,
    outcome: GameOutcome | None = None,
    own_role: Role | None = None,
    opponent_audit: dict[str, Any] | None = None,
    opponent_game_uid: str | None = None,
) -> dict[str, Any]:
    """The per-sub-game record. Carries the sub-game's outcome as well as its
    moves, because `result_<game_id>.json` is a MATCH-level file (book Table 20)
    that every sub-game would otherwise overwrite -- leaving the series report
    with no per-sub-game outcome to score from.
    """
    return {
        "game_id": game_id,
        "sub_game_number": sub_game_number,
        "outcome": outcome.value if outcome is not None else None,
        "own_role": own_role.value if own_role is not None else None,
        "moves": [
            {"turn": e.turn, "payload": e.payload, "nonce": e.nonce, "commitment": e.commitment}
            for e in commit_log.entries()
        ],
        "audit_passed": commit_log.audit(),
        "opponent_audit": opponent_audit,
        "opponent_game_uid": opponent_game_uid,
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
