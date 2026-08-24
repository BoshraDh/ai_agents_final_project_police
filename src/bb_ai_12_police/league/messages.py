"""Pure builders for the league kit's wire message shapes — kept separate
from `runtime.py` so the orchestration logic doesn't drown in dict
literals. Field names/shapes are pinned exactly to what SMNGRP05
specified (verified against their message, not guessed).
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from bb_ai_12_police.crypto.commit_reveal import CommitRevealLog
from bb_ai_12_police.crypto.step0 import Step0Declaration
from bb_ai_12_police.domain.pheromones import PheromoneField
from bb_ai_12_police.domain.protocol import Position, Role
from bb_ai_12_police.league.smell import serialize_smell_grid


def build_negotiate(
    terms: dict,
    nonce: str,
    signature: str,
    group_id: str,
    members: list[str],
    role: str,
    sub_game_number: int,
) -> dict:
    return {
        "terms": terms,
        "nonce": nonce,
        "signature": signature,
        "group_id": group_id,
        "identity": {"group_id": group_id, "members": members},
        "role": role,
        "sub_game_number": sub_game_number,
    }


def build_turn(
    step: int,
    role: Role,
    hint: str,
    own_scent: PheromoneField,
    commit: str,
    capture_claim: Position | None = None,
    claim_response: dict[str, Any] | None = None,
    win_claim: dict[str, Any] | None = None,
) -> dict[str, Any]:
    message: dict[str, Any] = {
        "step": step,
        "sender": role.value,
        "hint": hint,
        "smell_grid": serialize_smell_grid(own_scent),
        "commit": commit,
        "timestamp": dt.datetime.now(dt.UTC).isoformat(),
    }
    if capture_claim is not None:
        message["capture_claim"] = [capture_claim.row, capture_claim.col]
    if claim_response is not None:
        message["claim_response"] = claim_response
    if win_claim is not None:
        message["win_claim"] = win_claim
    return message


def build_audit(
    role: Role, log: CommitRevealLog, result_claim: str, step0: Step0Declaration
) -> dict:
    system_record = {
        "payload": {"type": "system_spec", **step0.payload},
        "nonce": step0.nonce,
        "commit": step0.commitment,
    }
    move_records = [
        {"payload": e.payload, "nonce": e.nonce, "commit": e.commitment} for e in log.entries()
    ]
    return {
        "sender": role.value,
        "records": [system_record, *move_records],
        "result_claim": result_claim,
    }
