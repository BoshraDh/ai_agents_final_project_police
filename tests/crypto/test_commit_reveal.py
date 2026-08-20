"""Tests for the SHA-256 commit-reveal primitives and audit log."""

from __future__ import annotations

import hashlib

from bb_ai_12_police.crypto.commit_reveal import (
    CommitRevealLog,
    canonical_json,
    compute_commitment,
    generate_nonce,
    verify_reveal,
)


def test_compute_commitment_matches_the_books_exact_formula():
    """Hcommit = SHA256(canonical_json({...payload, "nonce": nonce})) — book ch.5.3.

    The nonce is one more field inside the single canonically-serialized
    record, not concatenated onto the JSON string separately.
    """
    payload = {"state": "s0", "move": "N", "intent": "truth"}
    nonce = "deadbeef"
    expected = hashlib.sha256(
        canonical_json({**payload, "nonce": nonce}).encode("utf-8")
    ).hexdigest()
    assert compute_commitment(payload, nonce) == expected


def test_canonical_json_sorts_keys_and_strips_whitespace():
    assert canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'


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
