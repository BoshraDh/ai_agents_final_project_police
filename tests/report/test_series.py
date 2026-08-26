"""Tests for the match-level report.

These exist because the two things they guard both bit us live: a series was
filed with the bare sub-game sum (45-45 instead of 47-47), and `result_<game_id>
.json` is a match-level filename that every sub-game's own report overwrites.
"""

from __future__ import annotations

import json

import pytest

from bb_ai_12_police.report.series import (
    IncompleteSeriesError,
    build_final_result,
    collect_sub_game_logs,
    series_attachments,
    write_final_result,
)

US, THEM, GAME = "bb-ai-12", "SMNGRP05", "SMNGRP05-vs-bb-ai-12-20260826-2036"


def _log(number: int, outcome: str = "survived") -> dict:
    return {
        "game_id": GAME,
        "sub_game_number": number,
        "outcome": outcome,
        "own_role": "thief" if number % 2 == 1 else "police",
        "moves": [],
        "audit_passed": True,
    }


def _write_logs(tmp_path, numbers, outcome="survived"):
    target = tmp_path / US
    target.mkdir(parents=True, exist_ok=True)
    for n in numbers:
        (target / f"log_{GAME}_g{n:02d}.json").write_text(
            json.dumps(_log(n, outcome)), encoding="utf-8"
        )
    return tmp_path


def test_collect_orders_the_sub_games_numerically(tmp_path):
    _write_logs(tmp_path, [3, 1, 2])
    logs = collect_sub_game_logs(tmp_path, US, GAME)
    assert [entry["sub_game_number"] for entry in logs] == [1, 2, 3]


def test_a_full_series_scores_47_47_with_the_tie_award(tmp_path):
    _write_logs(tmp_path, range(1, 7))
    logs = collect_sub_game_logs(tmp_path, US, GAME)

    report = build_final_result(GAME, US, THEM, logs, expected_sub_games=6)

    assert report["report_type"] == "final_game_result"
    assert report["final_result"]["sub_game_totals"] == {US: 45, THEM: 45}
    assert report["final_result"]["total_score"] == {US: 47, THEM: 47}
    assert report["final_result"]["tie_award_applied"] is True
    assert report["final_result"]["series_tie"] is True
    assert report["final_result"]["winner_group"] is None
    assert [s["sub_game_number"] for s in report["sub_games"]] == [1, 2, 3, 4, 5, 6]
    assert report["sub_games"][0]["log_file"] == f"log_{GAME}_g01.json"


def test_a_short_series_is_refused_not_filed(tmp_path):
    _write_logs(tmp_path, range(1, 5))
    logs = collect_sub_game_logs(tmp_path, US, GAME)
    with pytest.raises(IncompleteSeriesError, match="4 of 6"):
        build_final_result(GAME, US, THEM, logs, expected_sub_games=6)


def test_an_unfinished_sub_game_is_refused_rather_than_scored_as_a_loss(tmp_path):
    _write_logs(tmp_path, range(1, 6))
    target = tmp_path / US
    (target / f"log_{GAME}_g06.json").write_text(
        json.dumps(_log(6, "ongoing")), encoding="utf-8"
    )
    logs = collect_sub_game_logs(tmp_path, US, GAME)
    with pytest.raises(IncompleteSeriesError, match="never finished"):
        build_final_result(GAME, US, THEM, logs, expected_sub_games=6)


def test_a_sub_game_with_no_recorded_outcome_is_refused(tmp_path):
    _write_logs(tmp_path, range(1, 6))
    target = tmp_path / US
    blank = _log(6)
    blank["outcome"] = None
    (target / f"log_{GAME}_g06.json").write_text(json.dumps(blank), encoding="utf-8")
    logs = collect_sub_game_logs(tmp_path, US, GAME)
    with pytest.raises(IncompleteSeriesError, match="reported no outcome"):
        build_final_result(GAME, US, THEM, logs, expected_sub_games=6)


def test_the_match_result_overwrites_the_per_sub_game_one(tmp_path):
    # Every sub-game's emit_report writes its own outcome into this same
    # match-level filename, so the last writer must be the match report.
    target = tmp_path / US
    target.mkdir(parents=True)
    stale = target / f"result_{GAME}.json"
    stale.write_text(json.dumps({"sub_game_number": 6, "outcome": "survived"}), encoding="utf-8")

    _write_logs(tmp_path, range(1, 7))
    logs = collect_sub_game_logs(tmp_path, US, GAME)
    written = write_final_result(
        tmp_path, US, GAME, build_final_result(GAME, US, THEM, logs, expected_sub_games=6)
    )

    assert written == stale
    reloaded = json.loads(written.read_text(encoding="utf-8"))
    assert reloaded["report_type"] == "final_game_result"
    assert reloaded["final_result"]["total_score"] == {US: 47, THEM: 47}


def test_attachments_gather_every_file_for_this_game_only(tmp_path):
    _write_logs(tmp_path, range(1, 7))
    target = tmp_path / US
    (target / f"declaration_{GAME}.json").write_text("{}", encoding="utf-8")
    (target / "log_some-other-game_g01.json").write_text("{}", encoding="utf-8")

    names = [p.name for p in series_attachments(tmp_path, US, GAME)]

    assert f"declaration_{GAME}.json" in names
    assert len([n for n in names if n.startswith("log_")]) == 6
    assert "log_some-other-game_g01.json" not in names
