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
    assert inbox.wait_for_negotiate(1.0)["terms"] == {}
    assert inbox.wait_for_audit(1.0)["sender"] == "police"
