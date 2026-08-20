"""Tests for the game_id/filename helpers."""

from __future__ import annotations

from bb_ai_12_police.domain.game_ids import artifact_filename, generate_game_id


def test_generate_game_id_starts_with_the_team_code():
    game_id = generate_game_id("bb-ai-12")
    assert game_id.startswith("bb-ai-12_")


def test_generate_game_id_is_unique_across_calls():
    assert generate_game_id("bb-ai-12") != generate_game_id("bb-ai-12")


def test_artifact_filename_declaration_and_result_have_no_sub_game_suffix():
    assert artifact_filename("declaration", "g1") == "declaration_g1.json"
    assert artifact_filename("result", "g1") == "result_g1.json"


def test_artifact_filename_config_and_log_include_a_zero_padded_sub_game_number():
    assert artifact_filename("config", "g1", 1) == "config_g1_g01.json"
    assert artifact_filename("log", "g1", 12) == "log_g1_g12.json"
