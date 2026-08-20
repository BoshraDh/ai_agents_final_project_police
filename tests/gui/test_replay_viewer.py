"""Tests for the replay viewer's audit re-verification and GUI smoke test."""

from __future__ import annotations

import json

from bb_ai_12_police.crypto.commit_reveal import compute_commitment, generate_nonce
from bb_ai_12_police.gui.replay_viewer import ReplayViewer, load_log, verify_move


def _sealed_move(turn: int, direction: str) -> dict:
    payload = {"direction": direction, "turn": turn}
    nonce = generate_nonce()
    return {
        "turn": turn,
        "payload": payload,
        "nonce": nonce,
        "commitment": compute_commitment(payload, nonce),
    }


def test_load_log_reads_back_valid_json(tmp_path):
    log_path = tmp_path / "log_g1_g01.json"
    log_path.write_text(json.dumps({"game_id": "g1", "sub_game_number": 1, "moves": []}))
    assert load_log(log_path) == {"game_id": "g1", "sub_game_number": 1, "moves": []}


def test_verify_move_is_true_for_an_untampered_move():
    assert verify_move(_sealed_move(1, "N"))


def test_verify_move_is_false_for_a_tampered_move():
    move = _sealed_move(1, "N")
    move["payload"]["direction"] = "S"
    assert not verify_move(move)


def test_replay_viewer_constructs_steps_through_and_closes_without_error():
    log = {
        "game_id": "bb-ai-12_abcd",
        "sub_game_number": 1,
        "moves": [_sealed_move(1, "N"), _sealed_move(2, "S")],
    }
    viewer = ReplayViewer(log, show=False)
    try:
        assert viewer.index == 0
        viewer.next_move()
        assert viewer.index == 1
        viewer.next_move()  # already at the last move; stays put
        assert viewer.index == 1
    finally:
        viewer.close()


def test_replay_viewer_handles_an_empty_log_without_error():
    viewer = ReplayViewer({"game_id": "g1", "sub_game_number": 1, "moves": []}, show=False)
    viewer.close()
