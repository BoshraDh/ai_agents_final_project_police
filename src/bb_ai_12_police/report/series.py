"""The match-level report: one `result_<game_id>.json`, one email, on a full series.

`emit_report` writes the per-sub-game artifacts. This module closes the match:
it collects the six sub-game logs, scores them with `domain.scoring`, writes the
MATCH-level result file that Table 20 (book p.141) defines, and sends a single
email with every artifact attached.

Two rules are enforced here rather than left to the caller:

- **Nothing is sent unless the whole series completed.** A partial match is not
  a match; the artifacts stay on disk and the series is replayed instead.
- **`result_<game_id>.json` is a match file.** Every sub-game's `emit_report`
  overwrites it with its own outcome, so the true match result is written last,
  from here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bb_ai_12_police.domain.game_ids import artifact_filename
from bb_ai_12_police.domain.protocol import GameOutcome, Role
from bb_ai_12_police.domain.scoring import score_series, sub_game_scores


class IncompleteSeriesError(RuntimeError):
    """Raised instead of filing a match that did not finish."""


def collect_sub_game_logs(logs_dir: Path, group_id: str, game_id: str) -> list[dict[str, Any]]:
    """Every `log_<game_id>_g<NN>.json` on disk, ordered by sub-game number."""
    target = logs_dir / group_id
    logs = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(target.glob(f"log_{game_id}_g*.json"))
    ]
    return sorted(logs, key=lambda entry: entry.get("sub_game_number", 0))


def series_attachments(logs_dir: Path, group_id: str, game_id: str) -> list[Path]:
    """Declaration, per-sub-game configs and logs, and the match result."""
    target = logs_dir / group_id
    return sorted(p for p in target.glob(f"*{game_id}*.json"))


def build_final_result(
    game_id: str,
    group_id: str,
    opponent_group: str,
    sub_game_logs: list[dict[str, Any]],
    expected_sub_games: int,
) -> dict[str, Any]:
    """The match-level `final_game_result`, scored from the per-sub-game logs.

    Raises `IncompleteSeriesError` if any sub-game is missing or unfinished --
    a technical loss is a real outcome and scores 0, but a sub-game that never
    reported one is absent data, and filing it as a loss would invent a result.
    """
    if len(sub_game_logs) != expected_sub_games:
        raise IncompleteSeriesError(
            f"{len(sub_game_logs)} of {expected_sub_games} sub-games on disk for {game_id}"
        )

    per_sub_game, entries = [], []
    for log in sub_game_logs:
        number = log.get("sub_game_number")
        outcome_value, role_value = log.get("outcome"), log.get("own_role")
        if outcome_value is None or role_value is None:
            raise IncompleteSeriesError(f"sub-game {number} of {game_id} reported no outcome")
        outcome, own_role = GameOutcome(outcome_value), Role(role_value)
        if outcome is GameOutcome.ONGOING:
            raise IncompleteSeriesError(f"sub-game {number} of {game_id} never finished")
        scores = sub_game_scores(outcome, own_role, group_id, opponent_group)
        per_sub_game.append(scores)
        entries.append(
            {
                "sub_game_number": number,
                "roles": {group_id: own_role.value},
                "result": outcome.value,
                "score": scores,
                "our_records_verified": log.get("audit_passed"),
                "opponent_audit": log.get("opponent_audit"),
                "log_file": artifact_filename("log", game_id, number),
            }
        )

    series = score_series(per_sub_game)
    return {
        "schema_version": "1.1",
        "report_type": "final_game_result",
        "game_id": game_id,
        "groups": sorted([group_id, opponent_group]),
        "num_sub_games": expected_sub_games,
        "reported_by": group_id,
        "sub_games": entries,
        "final_result": {
            "sub_game_totals": series.sub_game_totals,
            "tie_award_applied": series.tie_award_applied,
            "total_score": series.total_score,
            "winner_group": series.winner_group,
            "series_tie": series.series_tie,
        },
        "opponent_audit": _aggregate_opponent_audit(sub_game_logs),
    }


def _aggregate_opponent_audit(sub_game_logs: list[dict[str, Any]]) -> dict[str, Any]:
    """Series totals for the opponent's sealed records, summed from the sub-games.

    `all_verified` is true only when records were actually seen AND none failed,
    so a series where the opponent's audit never arrived reports `None` rather
    than a clean-looking true.
    """
    received = verified = failed = 0
    seen_any = False
    for log in sub_game_logs:
        audit = log.get("opponent_audit") or {}
        received += audit.get("received", 0)
        verified += audit.get("verified", 0)
        failed += audit.get("failed", 0)
        seen_any = seen_any or audit.get("all_verified") is not None
    return {
        "records_received": received,
        "records_verified": verified,
        "records_failed": failed,
        "all_verified": (received > 0 and failed == 0) if seen_any else None,
    }


def write_final_result(
    logs_dir: Path, group_id: str, game_id: str, final_result: dict[str, Any]
) -> Path:
    """Overwrites `result_<game_id>.json` with the MATCH result.

    Each sub-game's `emit_report` has already written its own outcome into this
    same match-level filename, so the last writer must be this one.
    """
    target = logs_dir / group_id
    target.mkdir(parents=True, exist_ok=True)
    path = target / artifact_filename("result", game_id)
    path.write_text(json.dumps(final_result, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
