"""`league-peer` — play one sub-game over the league kit's 4-tool wire
protocol (negotiate/receive_turn/submit_audit/receive_control), for
opponents that run that shape instead of this repo's own
submit_commit/submit_reveal. See `docs/PRD_league_adapter.md`.
"""

from __future__ import annotations

import asyncio
import os
import sys
import threading
import time
import traceback
from pathlib import Path

from bb_ai_12_police.crypto.step0 import Step0Declaration
from bb_ai_12_police.domain.barriers import BarrierSet
from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.pheromones import PheromoneField
from bb_ai_12_police.domain.protocol import GameOutcome, Role
from bb_ai_12_police.league.client import LeagueTransport
from bb_ai_12_police.league.inbox import LeagueInbox
from bb_ai_12_police.league.runtime import LeagueRuntime
from bb_ai_12_police.league.server_ready import wait_until_serving
from bb_ai_12_police.league.server_tools import add_league_tools
from bb_ai_12_police.league.terms import terms_signature, to_wire_terms
from bb_ai_12_police.llm.resolve_provider import resolve_provider
from bb_ai_12_police.mcp.server import build_server, run_server
from bb_ai_12_police.peer.turn_handler import TurnHandler
from bb_ai_12_police.report.emit import emit_report
from bb_ai_12_police.shared.config_manager import ConfigManager
from bb_ai_12_police.strategy.resolve_brain import resolve_brain

# This process exits right after asyncio.run(_play(...)) returns and kills
# the (daemon) server thread with it; linger briefly so the opponent's own
# in-flight submit_audit call -- sent just after they finish their own last
# turn -- still finds a live server instead of a dead port. Same fix already
# applied to cli/peer.py's book-protocol path (2026-08-20); never ported to
# this league-adapter path until now, found live 2026-08-25 (aviayeli's
# submit_audit to us got a 502 right after our sub-game 1 finished).
_SHUTDOWN_GRACE_SEC = 5.0


def _exit(code: int) -> None:
    # The daemon MCP-server thread is supposed to die with the process, but
    # was found live (2026-08-26 vs SMNGRP05) to sometimes leave the
    # interpreter running after this function would otherwise return or
    # raise -- real zombie processes stayed LISTENING on my_port minutes
    # later, still answering a live opponent with stale state. Force a real
    # exit instead of trusting normal shutdown. Only reached from the real
    # CLI path -- tests always monkeypatch `league_peer.run` itself, never
    # execute this function body, so this never fires under pytest.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)


def run(
    repo_root: str,
    turns: int,
    opponent_url: str | None,
    sub_game: int | None,
    friendly: bool = False,
    report_to: str | None = None,
    game_id: str | None = None,
    defer_report: bool = False,
) -> int:
    cfg = ConfigManager(repo_root)
    shared = cfg.load_shared()
    private = cfg.load_private()
    net = private["network"]
    group_id = private["game"]["group_id"]
    sub_game_number = sub_game if sub_game is not None else int(private["game"]["sub_game_number"])

    step0 = Step0Declaration.create(group_id)
    terms = to_wire_terms(shared)
    # A bare {"ok": True} negotiate reply left an opponent's handshake unable
    # to counter-verify us (no terms/nonce/signature to check against) --
    # found live 2026-08-25 (aviayeli's settlement record: handshake=
    # UNVERIFIED). Reuses the same nonce/signature this peer's own outbound
    # negotiate() call sends, so both are consistent with one real handshake.
    negotiate_reply = {
        "status": "accepted",
        "terms": terms,
        "nonce": step0.nonce,
        "signature": terms_signature(terms, step0.nonce),
        "role": Role.POLICE.value,
        "sub_game_number": sub_game_number,
    }

    turn_handler = TurnHandler()
    inbox = LeagueInbox()
    mcp = build_server(group_id, turn_handler)
    add_league_tools(mcp, inbox, negotiate_reply)
    thread = threading.Thread(
        target=run_server, args=(mcp, "127.0.0.1", net["my_port"]), daemon=True
    )
    thread.start()
    if not wait_until_serving(net["my_port"]):
        print(f"[league] our MCP route never came up on port {net['my_port']}; aborting")
        _exit(1)

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
        step0=step0,
        turn_timeout_sec=float(net["turn_timeout_seconds"]),
    )
    try:
        asyncio.run(_play(runtime, turns, sub_game_number))
    except Exception:  # noqa: BLE001 - print like an uncaught exception would, then hard-exit
        traceback.print_exc()
        _exit(1)
    time.sleep(_SHUTDOWN_GRACE_SEC)
    if runtime.outcome is GameOutcome.ONGOING:
        _exit(0)
    if defer_report:
        # Write the artifacts, send nothing: the match-level report goes out
        # once, from `series-report`, and only if all sub-games completed.
        recipient = private["email"]["recipient"]
    elif report_to:
        # Explicit override always wins: e.g. a validation send to the team's
        # own inboxes for an uncounted dry run, never the configured grader
        # address unless report_to is that address itself.
        recipient = report_to
    elif friendly:
        print("[report] --friendly: skipping the automatic report email (uncounted game).")
        _exit(0)
    else:
        recipient = private["email"]["recipient"]
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
        recipient=recipient,
        token_path=Path(repo_root) / "token.json",
        game_id=game_id,
        send=not defer_report,
        opponent_audit_payload=runtime.inbox.audit,
    )
    _exit(0)


async def _play(runtime: LeagueRuntime, turns: int, sub_game_number: int) -> None:
    async with runtime.transport:
        agreed = await runtime.negotiate(sub_game_number)
        print(f"negotiate: terms {'match' if agreed else 'DO NOT MATCH'} the opponent's")
        outcome = await runtime.play(turns)
        print(f"league game outcome: {outcome.value} (final_turn={runtime.final_turn})")
