"""Tests for the SHA-256 commit-reveal primitives and audit log."""

from __future__ import annotations

import hashlib

from bb_ai_12_police.crypto.commit_reveal import (
    CommitRevealLog,
    canonical_json,
    compute_commitment,
    generate_nonce,
    verify_opponent_records,
    verify_reveal,
)


def test_compute_commitment_matches_the_league_kits_exact_formula():
    """Hcommit = SHA256(canonical_json(payload) + "|" + nonce) — league kit formula.

    Deliberately NOT the book's ch.5.3 formula (nonce inside the JSON) —
    see the module docstring for why this repo follows the league's
    shared kit convention instead.
    """
    payload = {"state": "s0", "move": "N", "intent": "truth"}
    nonce = "deadbeef"
    expected = hashlib.sha256(f"{canonical_json(payload)}|{nonce}".encode()).hexdigest()
    assert compute_commitment(payload, nonce) == expected


def test_canonical_json_sorts_keys_and_strips_whitespace():
    assert canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_canonical_json_does_not_escape_non_ascii():
    assert canonical_json({"hint": "לא תפסת אותי"}) == '{"hint":"לא תפסת אותי"}'


def test_generate_nonce_returns_distinct_hex_strings():
    a, b = generate_nonce(), generate_nonce()
    assert a != b
    assert len(a) == 32
    int(a, 16)  # raises if not valid hex


def test_verify_reveal_succeeds_for_the_original_payload():
    payload = {"direction": "N", "turn": 1}
    nonce = generate_nonce()
    commitment = compute_commitment(payload, nonce)
    assert verify_reveal(payload, nonce, commitment)


def test_verify_reveal_fails_for_a_tampered_payload():
    payload = {"direction": "N", "turn": 1}
    nonce = generate_nonce()
    commitment = compute_commitment(payload, nonce)
    tampered = {"direction": "S", "turn": 1}
    assert not verify_reveal(tampered, nonce, commitment)


def test_commit_reveal_log_audit_passes_when_untouched():
    log = CommitRevealLog()
    log.seal(1, {"direction": "N", "turn": 1})
    log.seal(2, {"direction": "S", "turn": 2})
    assert log.audit()
    assert log.tampered_turns() == []


def test_commit_reveal_log_audit_catches_a_tampered_entry():
    log = CommitRevealLog()
    sealed = log.seal(1, {"direction": "N", "turn": 1})
    sealed.payload["direction"] = "S"  # simulate post-hoc tampering
    assert not log.audit()
    assert log.tampered_turns() == [1]


def test_entries_returns_a_snapshot_not_a_live_view():
    log = CommitRevealLog()
    log.seal(1, {"direction": "N", "turn": 1})
    snapshot = log.entries()
    log.seal(2, {"direction": "S", "turn": 2})
    assert len(snapshot) == 1
    assert len(log.entries()) == 2


def _their_records(count: int) -> list[dict]:
    """Records shaped exactly as SMNGRP05's `submit_audit` sends them."""
    log = CommitRevealLog()
    for turn in range(1, count + 1):
        log.seal(turn, {"step": turn, "direction": "N"})
    return [
        {"payload": e.payload, "nonce": e.nonce, "commit": e.commitment}
        for e in log.entries()
    ]


def test_verify_opponent_records_accepts_an_untampered_audit():
    result = verify_opponent_records({"sender": "SMNGRP05", "records": _their_records(35)})
    assert result == {"received": 35, "verified": 35, "failed": 0, "all_verified": True}


def test_verify_opponent_records_catches_a_tampered_payload():
    # The point of commit-reveal: the revealed move is not the committed one.
    records = _their_records(3)
    records[1]["payload"] = {"step": 2, "direction": "S"}
    result = verify_opponent_records({"records": records})
    assert result["verified"] == 2
    assert result["failed"] == 1
    assert result["all_verified"] is False


def test_verify_opponent_records_reports_a_missing_audit_as_unknown():
    # Not "clean": an audit that never arrived must not read as verified.
    assert verify_opponent_records(None)["all_verified"] is None
    assert verify_opponent_records({"records": []})["all_verified"] is None


def test_verify_opponent_records_counts_a_malformed_record_without_crashing():
    records = _their_records(2)
    records.append({"payload": {"step": 3}})  # no nonce, no commit
    result = verify_opponent_records({"records": records})
    assert result["received"] == 3
    assert result["verified"] == 2
    assert result["failed"] == 1
