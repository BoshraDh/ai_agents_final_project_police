"""Tests for the four mandatory JSON artifact builders."""

from __future__ import annotations

from bb_ai_12_police.crypto.commit_reveal import CommitRevealLog
from bb_ai_12_police.crypto.step0 import Step0Declaration
from bb_ai_12_police.domain.protocol import GameOutcome, Role
from bb_ai_12_police.report.artifacts import (
    build_config,
    build_declaration,
    build_log,
    build_result,
)


def test_build_declaration_carries_the_sealed_fields():
    step0 = Step0Declaration.create("bb-ai-12")
    artifact = build_declaration(step0)
    assert artifact == {
        "payload": step0.payload,
        "nonce": step0.nonce,
        "commitment": step0.commitment,
    }


def test_build_config_carries_the_shared_config_and_its_hash():
    shared = {"board_and_agents": {"grid_size": 7}}
    artifact = build_config(shared, "deadbeef")
    assert artifact["shared_config"] == shared
    assert artifact["shared_config_sha256"] == "deadbeef"


def test_build_log_reports_moves_and_audit_status():
    log = CommitRevealLog()
    log.seal(1, {"direction": "N", "turn": 1})
    log.seal(2, {"direction": "S", "turn": 2})
    artifact = build_log("bb-ai-12_abcd", 1, log)
    assert artifact["game_id"] == "bb-ai-12_abcd"
    assert artifact["sub_game_number"] == 1
    assert len(artifact["moves"]) == 2
    assert artifact["audit_passed"] is True


def test_build_log_flags_a_tampered_entry_as_audit_failed():
    log = CommitRevealLog()
    sealed = log.seal(1, {"direction": "N", "turn": 1})
    sealed.payload["direction"] = "S"
    artifact = build_log("bb-ai-12_abcd", 1, log)
    assert artifact["audit_passed"] is False


def test_build_result_reports_the_fixed_scores_for_the_outcome():
    artifact = build_result("bb-ai-12_abcd", 1, GameOutcome.CAPTURED, Role.POLICE)
    assert artifact["outcome"] == "captured"
    assert artifact["scores"] == {"police": 20, "thief": 5}
    assert artifact["reported_by"] == "police"


def test_build_log_carries_the_sub_game_outcome_and_role():
    # The series report scores from these: result_<game_id>.json is a
    # match-level file that every sub-game overwrites, so the per-sub-game
    # outcome has to live in the per-sub-game log or it is lost.
    log = CommitRevealLog()
    log.seal(1, {"direction": "N", "turn": 1})
    artifact = build_log("SMNGRP05-vs-bb-ai-12", 4, log, GameOutcome.SURVIVED, Role.POLICE)
    assert artifact["outcome"] == "survived"
    assert artifact["own_role"] == "police"


def test_build_log_leaves_outcome_null_when_not_supplied():
    artifact = build_log("SMNGRP05-vs-bb-ai-12", 4, CommitRevealLog())
    assert artifact["outcome"] is None
    assert artifact["own_role"] is None
