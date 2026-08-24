"""`league-peer` — play one sub-game over the league kit's 4-tool wire
protocol (negotiate/receive_turn/submit_audit/receive_control), for
opponents that run that shape instead of this repo's own
submit_commit/submit_reveal. See `docs/PRD_league_adapter.md`.
"""

from __future__ import annotations

import asyncio
import threading
import time
from pathlib import Path

from bb_ai_12_police.crypto.step0 import Step0Declaration
from bb_ai_12_police.domain.barriers import BarrierSet
from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.pheromones import PheromoneField
from bb_ai_12_police.domain.protocol import GameOutcome, Role
from bb_ai_12_police.league.client import LeagueTransport
from bb_ai_12_police.league.inbox import LeagueInbox
from bb_ai_12_police.league.runtime import LeagueRuntime
from bb_ai_12_police.league.server_tools import add_league_tools
from bb_ai_12_police.llm.resolve_provider import resolve_provider
from bb_ai_12_police.mcp.server import build_server, run_server
from bb_ai_12_police.peer.turn_handler import TurnHandler
from bb_ai_12_police.report.emit import emit_report
from bb_ai_12_police.shared.config_manager import ConfigManager
from bb_ai_12_police.strategy.resolve_brain import resolve_brain


def run(repo_root: str, turns: int, opponent_url: str | None, sub_game: int | None) -> int:
    cfg = ConfigManager(repo_root)
    shared = cfg.load_shared()
    private = cfg.load_private()
    net = private["network"]
    group_id = private["game"]["group_id"]
    sub_game_number = sub_game if sub_game is not None else int(private["game"]["sub_game_number"])

    turn_handler = TurnHandler()
    inbox = LeagueInbox()
    mcp = build_server(group_id, turn_handler)
    add_league_tools(mcp, inbox)
    thread = threading.Thread(
        target=run_server, args=(mcp, "127.0.0.1", net["my_port"]), daemon=True
    )
    thread.start()
    time.sleep(1.0)

    board = Board.from_config(shared)
    runtime = LeagueRuntime(
        role=Role.POLICE,
        own_position=board.start_position("cop_start", shared),
        opponent_start=board.start_position("thief_start", shared),
        board=board,
        barriers=BarrierSet.from_config(shared),
        brain=resolve_brain(private),
        trash_talk=resolve_provider(private, shared),
        own_scent=PheromoneField.from_config(shared),
        survival_threshold=shared["movement_and_barriers"]["survival_threshold"],
        shared_config=shared,
        group_id=group_id,
        members=private["game"]["members"],
        transport=LeagueTransport(opponent_url or net["opponent_url"]),
        inbox=inbox,
        step0=Step0Declaration.create(group_id),
    )
    asyncio.run(_play(runtime, turns, sub_game_number))
    if runtime.outcome is not GameOutcome.ONGOING:
        emit_report(
            logs_dir=Path(repo_root) / "logs",
            group_id=group_id,
            sub_game_number=sub_game_number,
            outcome=runtime.outcome,
            role=Role.POLICE,
            commit_log=runtime.commit_log,
            step0=runtime.step0,
            shared_config=shared,
            game_json_sha256=cfg.game_json_sha256(),
            recipient=private["email"]["recipient"],
            token_path=Path(repo_root) / "token.json",
        )
    return 0


async def _play(runtime: LeagueRuntime, turns: int, sub_game_number: int) -> None:
    async with runtime.transport:
        agreed = await runtime.negotiate(sub_game_number)
        print(f"negotiate: terms {'match' if agreed else 'DO NOT MATCH'} the opponent's")
        outcome = await runtime.play(turns)
        print(f"league game outcome: {outcome.value} (final_turn={runtime.final_turn})")
