"""`peer` — play real commit-reveal rounds against the opponent."""

from __future__ import annotations

from bb_ai_12_police.crypto.commit_reveal import CommitRevealLog
from bb_ai_12_police.domain.barriers import BarrierSet
from bb_ai_12_police.domain.belief import BeliefState
from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.pheromones import PheromoneField
from bb_ai_12_police.domain.protocol import Role
from bb_ai_12_police.llm.resolve_provider import resolve_provider
from bb_ai_12_police.peer.turn_handler import TurnHandler
from bb_ai_12_police.runtime.peer_runtime import PeerRuntime
from bb_ai_12_police.shared.config_manager import ConfigManager
from bb_ai_12_police.strategy.resolve_brain import resolve_brain


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
    return 0
