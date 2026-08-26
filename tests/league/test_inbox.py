"""Tests for LeagueInbox's blocking-wait behaviour."""

from __future__ import annotations

import threading
import time

import pytest

from bb_ai_12_police.league.inbox import LeagueInbox


def test_wait_for_turn_returns_immediately_if_already_received():
    inbox = LeagueInbox()
    inbox.receive_turn({"step": 1, "hint": "hi"})
    assert inbox.wait_for_turn(1, timeout_sec=1.0)["hint"] == "hi"


def test_wait_for_turn_blocks_until_another_thread_delivers_it():
    inbox = LeagueInbox()

    def deliver_soon():
        time.sleep(0.05)
        inbox.receive_turn({"step": 1, "hint": "delayed"})

    threading.Thread(target=deliver_soon).start()
    message = inbox.wait_for_turn(1, timeout_sec=1.0, poll_interval_sec=0.01)
    assert message["hint"] == "delayed"


def test_wait_for_turn_times_out_if_never_delivered():
    inbox = LeagueInbox()
    with pytest.raises(TimeoutError, match="timed out"):
        inbox.wait_for_turn(1, timeout_sec=0.05, poll_interval_sec=0.01)


def test_wait_for_negotiate_and_wait_for_audit_also_work():
    inbox = LeagueInbox()
    inbox.receive_negotiate({"terms": {}})
    inbox.receive_audit({"sender": "police"})
    assert inbox.wait_for_negotiate(1, 1.0)["terms"] == {}
    assert inbox.wait_for_audit(1.0)["sender"] == "police"


def test_a_stale_greeting_does_not_satisfy_a_wait_for_the_next_sub_game():
    """Regression test for the desync class chased live on 2026-08-26.

    The negotiated terms are byte-identical across all six sub-games, so a
    leftover greeting for sub-game 3 passed full terms+signature validation
    while we were opening sub-game 4. Keying by sub-game is what keeps a
    six-sub-game series in step.
    """
    inbox = LeagueInbox()
    inbox.receive_negotiate({"terms": {}, "sub_game_number": 3})
    with pytest.raises(TimeoutError):
        inbox.wait_for_negotiate(4, 0.05)
    assert inbox.wait_for_negotiate(3, 0.05)["sub_game_number"] == 3


def test_a_greeting_without_a_sub_game_number_is_filed_under_the_default():
    inbox = LeagueInbox()
    inbox.receive_negotiate({"terms": {}}, 5)
    assert inbox.wait_for_negotiate(5, 0.05)["terms"] == {}




def test_a_turn_without_a_step_is_dropped_not_raised():
    inbox = LeagueInbox()
    inbox.receive_turn({"sender": "police"})
    with pytest.raises(TimeoutError):
        inbox.wait_for_turn(1, 0.05)
