"""Tests for pure outcome-detection from one inbound league turn message."""

from __future__ import annotations

from bb_ai_12_police.domain.protocol import GameOutcome, Position, Role
from bb_ai_12_police.league.outcome import absorb_inbound, build_claim_response


def test_police_sees_captured_when_thief_confirms_caught():
    outcome, claim = absorb_inbound(
        Role.POLICE, survived_now=False, inbound={"claim_response": {"caught": True}}
    )
    assert outcome == GameOutcome.CAPTURED
    assert claim is None


def test_police_stays_ongoing_when_thief_denies_caught():
    outcome, _ = absorb_inbound(
        Role.POLICE, survived_now=False, inbound={"claim_response": {"caught": False}}
    )
    assert outcome == GameOutcome.ONGOING


def test_police_sees_survived_on_a_thief_win_claim():
    outcome, _ = absorb_inbound(
        Role.POLICE, survived_now=False, inbound={"win_claim": {"type": "survival"}}
    )
    assert outcome == GameOutcome.SURVIVED


def test_thief_buffers_a_pending_capture_claim_for_next_turn():
    outcome, claim = absorb_inbound(
        Role.THIEF, survived_now=False, inbound={"capture_claim": [3, 3]}
    )
    assert outcome == GameOutcome.ONGOING
    assert claim == [3, 3]


def test_thief_sees_survived_once_its_own_threshold_is_reached():
    outcome, _ = absorb_inbound(Role.THIEF, survived_now=True, inbound={})
    assert outcome == GameOutcome.SURVIVED


def test_build_claim_response_reports_caught_true_when_positions_match():
    response = build_claim_response([3, 3], own_position=Position(row=3, col=3))
    assert response == {"claim": [3, 3], "caught": True}


def test_build_claim_response_reports_caught_false_when_positions_differ():
    response = build_claim_response([3, 3], own_position=Position(row=0, col=0))
    assert response == {"claim": [3, 3], "caught": False}
