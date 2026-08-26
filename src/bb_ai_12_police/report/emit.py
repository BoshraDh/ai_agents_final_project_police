"""Orchestrates build -> write -> email for a finished game.

`PRD_reporting_shell.md` deferred a real `send-report` hook because no
caller had a real `GameOutcome` yet. `PeerRuntime`/`LeagueRuntime` now both
stop their turn loop with one, so `cli/peer.py` and `cli/league_peer.py`
call `emit_report` once, right after `outcome is not GameOutcome.ONGOING`.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from bb_ai_12_police.crypto.commit_reveal import CommitRevealLog
from bb_ai_12_police.crypto.step0 import Step0Declaration
from bb_ai_12_police.domain.game_ids import generate_game_id
from bb_ai_12_police.domain.protocol import GameOutcome, Role
from bb_ai_12_police.infra.email_sender import send_report
from bb_ai_12_police.report.artifacts import (
    build_config,
    build_declaration,
    build_log,
    build_result,
)
from bb_ai_12_police.report.report_writer import write_artifacts
from bb_ai_12_police.shared.api_gatekeeper import TokenBucketGatekeeper, run_guarded

logger = logging.getLogger(__name__)


def emit_report(
    *,
    logs_dir: Path,
    group_id: str,
    sub_game_number: int,
    outcome: GameOutcome,
    role: Role,
    commit_log: CommitRevealLog,
    step0: Step0Declaration,
    shared_config: dict[str, Any],
    game_json_sha256: str,
    recipient: str,
    token_path: Path,
    game_id: str | None = None,
) -> dict[str, Any] | None:
    """Builds and writes the four artifacts, then emails them to `recipient`.

    Returns the Gmail API response, or `None` if the send failed (logged,
    non-fatal -- a report failure must never crash a peer process after a
    real game outcome; the artifacts are already safely on disk by then).
    """
    # One game_id per MATCH, not per sub-game. Table 20 (book p.141) derives every
    # artifact filename from the game_id plus the sub-game number precisely "so
    # that files from different games are never mixed" -- minting a fresh random
    # id inside each sub-game produced six unrelated ids for one six-sub-game
    # series. A caller that has no series context still gets one generated.
    game_id = game_id or generate_game_id(group_id)
    declaration = build_declaration(step0)
    config = build_config(shared_config, game_json_sha256)
    log = build_log(game_id, sub_game_number, commit_log)
    result = build_result(game_id, sub_game_number, outcome, role)

    attachments = write_artifacts(
        logs_dir, group_id, game_id, sub_game_number, declaration, config, log, result
    )

    gatekeeper = TokenBucketGatekeeper.from_config(shared_config)
    subject = f"[{group_id}] game {game_id} sub-game {sub_game_number}: {outcome.value}"
    body = f"Automated report for {group_id} ({role.value}). Outcome: {outcome.value}."

    try:
        response = run_guarded(
            gatekeeper,
            lambda: send_report(token_path, recipient, subject, body, attachments),
        )
    except Exception:
        logger.exception(
            "emit_report: send_report failed; artifacts remain on disk at %s",
            attachments[0].parent,
        )
        return None
    print(f"[report] emailed {game_id} sub-game {sub_game_number} to {recipient}: {response!r}")
    return response
