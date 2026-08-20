"""Tests for the pre-game shared-config agreement check."""

from __future__ import annotations

from bb_ai_12_police.domain.negotiation import configs_match


def test_configs_match_when_hashes_are_identical():
    assert configs_match("abc123", "abc123")


def test_configs_match_is_false_when_hashes_differ():
    assert not configs_match("abc123", "def456")
