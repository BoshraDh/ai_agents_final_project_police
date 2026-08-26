"""`series-report`: file ONE match-level report for a finished series.

The book requires the closing report at the end of a GAME, not of each
sub-game (p.71), as a single machine-readable JSON attachment (p.78). This
subcommand collects the six sub-game artifacts written by `league-peer
--defer-report`, scores the match, writes `result_<game_id>.json`, and sends
one email carrying every artifact.

It refuses to send an incomplete series: a partial match is replayed, not filed.
"""

from __future__ import annotations

from pathlib import Path

from bb_ai_12_police.infra.email_sender import send_report
from bb_ai_12_police.report.series import (
    IncompleteSeriesError,
    build_final_result,
    collect_sub_game_logs,
    series_attachments,
    write_final_result,
)
from bb_ai_12_police.shared.config_manager import ConfigManager


def _body(report: dict, game_id: str, group_id: str, commit: str | None) -> str:
    final = report["final_result"]
    lines = [
        f"Final game result for {group_id}, game {game_id}.",
        "",
        f"Sub-games played: {report['num_sub_games']}",
        f"Sub-game totals: {final['sub_game_totals']}",
        f"Tie award applied: {final['tie_award_applied']}",
        f"Total score: {final['total_score']}",
        f"Winner: {final['winner_group'] or 'tie'}",
        "",
    ]
    # Mandatory rule 5 (book p.140): each game's email carries the GitHub
    # commit the code was at for that game.
    lines.append(f"GitHub commit used for this game: {commit or 'unknown'}")
    lines.append("")
    lines.append("The binding report is the attached JSON; this body is a summary only.")
    return "\n".join(lines)


def run(
    repo_root: str,
    game_id: str,
    opponent_group: str,
    report_to: str | None = None,
    dry_run: bool = False,
) -> int:
    cfg = ConfigManager(repo_root)
    shared = cfg.load_shared()
    private = cfg.load_private()
    group_id = private["game"]["group_id"]
    logs_dir = Path(repo_root) / "logs"
    expected = int(shared["network_and_league"]["num_games"])

    logs = collect_sub_game_logs(logs_dir, group_id, game_id)
    try:
        report = build_final_result(game_id, group_id, opponent_group, logs, expected)
    except IncompleteSeriesError as exc:
        print(f"[series-report] NOT filing: {exc}")
        print("[series-report] artifacts remain on disk; replay the series rather than file it.")
        return 1

    result_path = write_final_result(logs_dir, group_id, game_id, report)
    attachments = series_attachments(logs_dir, group_id, game_id)
    final = report["final_result"]
    print(f"[series-report] {result_path.name}: total {final['total_score']}, "
          f"tie_award={final['tie_award_applied']}, winner={final['winner_group'] or 'tie'}")
    print(f"[series-report] {len(attachments)} artifacts to attach")

    if dry_run:
        print("[series-report] --dry-run: nothing sent")
        return 0

    recipient = report_to or private["email"]["recipient"]
    commit = _git_commit(repo_root)
    subject = f"[{group_id}] final game result {game_id}: {final['total_score']}"
    try:
        response = send_report(
            token_path=Path(repo_root) / "token.json",
            recipient=recipient,
            subject=subject,
            body=_body(report, game_id, group_id, commit),
            attachments=attachments,
        )
    except Exception as exc:  # noqa: BLE001 - artifacts are already safe on disk
        print(f"[series-report] send FAILED: {exc!r}")
        print(f"[series-report] artifacts remain at {result_path.parent}")
        return 1
    print(f"[series-report] sent to {recipient}: {response}")
    return 0


def _git_commit(repo_root: str) -> str | None:
    import subprocess

    try:
        done = subprocess.run(
            ["git", "-C", repo_root, "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        )
    except Exception:  # noqa: BLE001 - reported as unknown rather than failing the filing
        return None
    return done.stdout.strip() or None
