"""Tests for the per-round turn protocol's local bookkeeping."""

from __future__ import annotations

import pytest

from bb_ai_12_police.peer.turn_handler import TurnHandler


def test_prepare_own_reveal_then_own_reveal_returns_it():
    handler = TurnHandler()
    handler.prepare_own_reveal(1, "N", "hi", "truth")
    reveal = handler.own_reveal(1)
    assert reveal.turn == 1
    assert reveal.move == "N"
    assert reveal.hint == "hi"
    assert reveal.intent == "truth"


def test_own_reveal_raises_if_not_prepared():
    handler = TurnHandler()
    with pytest.raises(ValueError, match="no own reveal prepared"):
        handler.own_reveal(1)


def test_receive_commit_then_has_received_commit_is_true():
    handler = TurnHandler()
    assert not handler.has_received_commit(1)
    handler.receive_commit(1, "abc123")
    assert handler.has_received_commit(1)


def test_receive_reveal_succeeds_after_a_commit_was_received():
    handler = TurnHandler()
    handler.receive_commit(1, "abc123")
    reveal = handler.receive_reveal(1, "S", "yo", "lie")
    assert handler.opponent_reveal(1) == reveal
    assert reveal.move == "S"


def test_receive_reveal_without_a_prior_commit_raises():
    handler = TurnHandler()
    with pytest.raises(ValueError, match="protocol violation"):
        handler.receive_reveal(1, "S", "yo", "lie")


def test_opponent_reveal_is_none_before_it_arrives():
    handler = TurnHandler()
    assert handler.opponent_reveal(1) is None
