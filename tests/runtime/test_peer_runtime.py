"""Tests for the real per-round commit-reveal turn loop — no real networking."""

from __future__ import annotations

from bb_ai_12_police.crypto.commit_reveal import CommitRevealLog
from bb_ai_12_police.domain.barriers import BarrierSet
from bb_ai_12_police.domain.belief import BeliefState
from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.pheromones import PheromoneField
from bb_ai_12_police.domain.protocol import Direction, Position
from bb_ai_12_police.llm.template_provider import TemplateProvider
from bb_ai_12_police.peer.turn_handler import TurnHandler
from bb_ai_12_police.runtime.peer_runtime import PeerRuntime
from bb_ai_12_police.strategy.police_brain import PoliceBrain

_PHEROMONE_CONFIG = {
    "pheromones": {
        "pheromone_center_intensity": 0.9,
        "pheromone_decay": 0.10,
        "pheromone_grid_size": 5,
    }
}


def _runtime() -> PeerRuntime:
    return PeerRuntime(
        host="127.0.0.1",
        port=9999,
        opponent_url="http://unused",
        server_name="bb-ai-12-police",
        board=Board(size=7),
        barriers=BarrierSet(max_barriers=14),
        belief=BeliefState(own_position=Position(0, 0), opponent_position=Position(3, 3)),
        brain=PoliceBrain(),
        trash_talk=TemplateProvider(hint_max_words=15),
        opponent_scent=PheromoneField.from_config(_PHEROMONE_CONFIG),
        commit_log=CommitRevealLog(),
        turn_handler=TurnHandler(),
    )


def _stub_transport(runtime: PeerRuntime, monkeypatch, opponent_move: str = "STAY") -> list:
    """Makes send_commit/send_reveal no-ops that pretend the opponent stayed put."""
    calls: list[tuple[str, tuple]] = []

    def fake_send_commit(h_commit: str, turn: int) -> dict:
        calls.append(("commit", (h_commit, turn)))
        return {"received": True, "turn": turn}

    def fake_send_reveal(move: str, hint: str, intent: str, turn: int) -> dict:
        calls.append(("reveal", (move, hint, intent, turn)))
        return {"move": opponent_move, "hint": "...", "intent": "truth", "turn": turn}

    monkeypatch.setattr(runtime.transport, "send_commit", fake_send_commit)
    monkeypatch.setattr(runtime.transport, "send_reveal", fake_send_reveal)
    return calls


def test_decide_move_uses_the_brain_to_chase_the_tracked_opponent():
    assert _runtime()._decide_move() == Direction.SOUTH


def test_run_turn_loop_completes_the_commit_reveal_cycle_each_round(monkeypatch):
    runtime = _runtime()
    calls = _stub_transport(runtime, monkeypatch)
    runtime.run_turn_loop(3)

    commits = [c for kind, c in calls if kind == "commit"]
    reveals = [c for kind, c in calls if kind == "reveal"]
    assert [turn for _, turn in commits] == [1, 2, 3]
    assert [turn for _, _, _, turn in reveals] == [1, 2, 3]
    assert all(hint for _, hint, _, _ in reveals)


def test_run_turn_loop_ends_in_waiting_for_opponent_each_round(monkeypatch):
    runtime = _runtime()
    _stub_transport(runtime, monkeypatch)
    runtime.run_turn_loop(2)
    assert runtime.machine.state == "WAITING_FOR_OPPONENT"


def test_run_turn_loop_seals_every_move_and_passes_audit(monkeypatch):
    runtime = _runtime()
    _stub_transport(runtime, monkeypatch)
    runtime.run_turn_loop(3)
    assert runtime.commit_log.audit()
    assert runtime.commit_log.tampered_turns() == []


def test_run_turn_loop_updates_belief_from_the_opponents_real_reveal(monkeypatch):
    runtime = _runtime()
    _stub_transport(runtime, monkeypatch, opponent_move="W")
    runtime.run_turn_loop(1)
    assert runtime.belief.opponent_position == Position(3, 2)


def test_a_failed_commit_send_moves_the_machine_to_technical_loss(monkeypatch):
    runtime = _runtime()

    def boom(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(runtime.transport, "send_commit", boom)
    try:
        runtime.run_turn_loop(1)
    except RuntimeError:
        pass
    assert runtime.machine.state == "TECHNICAL_LOSS"
