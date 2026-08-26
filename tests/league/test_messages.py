"""Tests for the league wire message builders."""

from __future__ import annotations

from bb_ai_12_police.crypto.commit_reveal import CommitRevealLog, compute_commitment
from bb_ai_12_police.crypto.step0 import Step0Declaration
from bb_ai_12_police.domain.pheromones import PheromoneField
from bb_ai_12_police.domain.protocol import Position, Role
from bb_ai_12_police.league.messages import build_audit, build_negotiate, build_turn

_SCENT_CONFIG = {"pheromones": {
    "pheromone_center_intensity": 0.9, "pheromone_decay": 0.1, "pheromone_grid_size": 5,
}}


def test_build_negotiate_nests_group_id_at_top_level_and_inside_identity():
    message = build_negotiate({"a": 1}, "nonce", "sig", "bb-ai-12", ["id-1", "id-2"], "police", 2)
    assert message["group_id"] == "bb-ai-12"
    assert message["identity"] == {"group_id": "bb-ai-12", "members": ["id-1", "id-2"]}
    assert message["role"] == "police"
    assert message["sub_game_number"] == 2


def test_build_turn_includes_required_fields_and_omits_unset_optionals():
    scent = PheromoneField.from_config(_SCENT_CONFIG)
    scent.step(Position(0, 0))
    message = build_turn(1, Role.POLICE, "hint text", scent, "deadbeef" * 8)
    assert message["step"] == 1
    assert message["sender"] == "police"
    assert message["smell_grid"] == {"0,0": 0.9}
    assert "capture_claim" not in message
    assert "claim_response" not in message
    assert "win_claim" not in message


def test_build_turn_includes_capture_claim_when_given():
    scent = PheromoneField.from_config(_SCENT_CONFIG)
    message = build_turn(
        1, Role.POLICE, "hint", scent, "commit", capture_claim=Position(row=3, col=3)
    )
    assert message["capture_claim"] == [3, 3]


def test_build_audit_puts_a_system_spec_record_first():
    log = CommitRevealLog()
    log.seal(1, {"move": "N"})
    step0 = Step0Declaration.create("bb-ai-12")
    envelope = build_audit("bb-ai-12", log, "survival", step0)
    assert envelope["sender"] == "bb-ai-12"
    assert envelope["result_claim"] == "survival"
    assert envelope["records"][0]["payload"]["type"] == "system_spec"
    assert len(envelope["records"]) == 2


def test_build_audit_sends_exactly_three_keys_and_a_string_claim():
    """Regression test for two defects found live (2026-08-26) vs SMNGRP05.

    `sender` carried `role.value` ("police"), so their server accepted the call
    but could not match the audit to our group and logged it as absent; and
    `result_claim` was a dict (`{"type": ...}`) where the kit expects a bare
    string. A fourth key is equally fatal: their `AuditPayload(**data)` raises
    TypeError on an unexpected key, killing an otherwise-valid sub-game.
    """
    log = CommitRevealLog()
    step0 = Step0Declaration.create("bb-ai-12")
    envelope = build_audit("bb-ai-12", log, "capture", step0)
    assert set(envelope) == {"sender", "records", "result_claim"}
    assert isinstance(envelope["result_claim"], str)


def test_build_audit_system_record_commit_verifies_against_the_wire_payload():
    """Regression test: a receiving auditor recomputes commit_of(payload, nonce)
    over exactly the payload it received. The system record's "payload" must
    therefore be byte-identical to what Step0Declaration actually sealed --
    found live (2026-08-24) as a real audit failure against SMNGRP05 when
    build_audit added a "type" key to the payload *after* sealing.
    """
    log = CommitRevealLog()
    step0 = Step0Declaration.create("bb-ai-12")
    envelope = build_audit("bb-ai-12", log, "capture", step0)
    record = envelope["records"][0]
    recomputed = compute_commitment(record["payload"], record["nonce"])
    assert recomputed == record["commit"]
