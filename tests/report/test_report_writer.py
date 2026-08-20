"""Tests for writing the four artifacts to `logs/<group_id>/`."""

from __future__ import annotations

import json

from bb_ai_12_police.report.report_writer import write_artifacts


def test_write_artifacts_creates_all_four_files_with_correct_names(tmp_path):
    paths = write_artifacts(
        tmp_path,
        group_id="bb-ai-12",
        game_id="bb-ai-12_abcd",
        sub_game_number=1,
        declaration={"a": 1},
        config={"b": 2},
        log={"c": 3},
        result={"d": 4},
    )
    names = {p.name for p in paths}
    assert names == {
        "declaration_bb-ai-12_abcd.json",
        "config_bb-ai-12_abcd_g01.json",
        "log_bb-ai-12_abcd_g01.json",
        "result_bb-ai-12_abcd.json",
    }
    for path in paths:
        assert path.parent == tmp_path / "bb-ai-12"


def test_write_artifacts_writes_valid_json_content(tmp_path):
    paths = write_artifacts(
        tmp_path,
        group_id="bb-ai-12",
        game_id="bb-ai-12_abcd",
        sub_game_number=1,
        declaration={"a": 1},
        config={"b": 2},
        log={"c": 3},
        result={"d": 4},
    )
    result_path = next(p for p in paths if p.name.startswith("result_"))
    assert json.loads(result_path.read_text(encoding="utf-8")) == {"d": 4}
