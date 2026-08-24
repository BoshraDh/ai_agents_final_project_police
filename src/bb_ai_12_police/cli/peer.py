"""`peer` — play real commit-reveal rounds against the opponent."""

from __future__ import annotations

import time
from pathlib import Path

from bb_ai_12_police.crypto.commit_reveal import CommitRevealLog
from bb_ai_12_police.crypto.step0 import Step0Declaration
from bb_ai_12_police.domain.barriers import BarrierSet
from bb_ai_12_police.domain.belief import BeliefState
from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.pheromones import PheromoneField
from bb_ai_12_police.domain.protocol import GameOutcome, Role
from bb_ai_12_police.llm.resolve_provider import resolve_provider
from bb_ai_12_police.peer.turn_handler import TurnHandler
from bb_ai_12_police.report.emit import emit_report
from bb_ai_12_police.runtime.peer_runtime import PeerRuntime
from bb_ai_12_police.shared.config_manager import ConfigManager
from bb_ai_12_police.strategy.resolve_brain import resolve_brain

_SHUTDOWN_GRACE_SEC = 3.0


def run(repo_root: str, turns: int) -> int:
    cfg = ConfigManager(repo_root)
    shared = cfg.load_shared()
    private = cfg.load_private()
    net = private["network"]

    runtime = PeerRuntime(
        host="127.0.0.1",
        port=net["my_port"],
        opponent_url=net["opponent_url"],
        server_name=private["game"]["group_id"],
        role=Role.POLICE,
        survival_threshold=shared["movement_and_barriers"]["survival_threshold"],
        reveal_wait_timeout_sec=shared["network_and_league"]["response_timeout_sec"],
        board=Board.from_config(shared),
        barriers=BarrierSet.from_config(shared),
        belief=BeliefState.from_config(shared, "cop_start", "thief_start"),
        brain=resolve_brain(private),
        trash_talk=resolve_provider(private, shared),
        opponent_scent=PheromoneField.from_config(shared),
        commit_log=CommitRevealLog(),
        turn_handler=TurnHandler(),
    )
    runtime.start_server()
    runtime.run_turn_loop(turns)
    if runtime.outcome is not GameOutcome.ONGOING:
        group_id = private["game"]["group_id"]
        emit_report(
            logs_dir=Path(repo_root) / "logs",
            group_id=group_id,
            sub_game_number=int(private["game"]["sub_game_number"]),
            outcome=runtime.outcome,
            role=Role.POLICE,
            commit_log=runtime.commit_log,
            step0=Step0Declaration.create(group_id),
            shared_config=shared,
            game_json_sha256=cfg.game_json_sha256(),
            recipient=private["email"]["recipient"],
            token_path=Path(repo_root) / "token.json",
        )
        # This process exits right after this and kills the (daemon) server
        # thread with it; linger briefly so the opponent's in-flight
        # final-round call -- which can arrive just after we declared the
        # game over -- still finds a live server instead of a dead port.
        time.sleep(_SHUTDOWN_GRACE_SEC)
    return 0
