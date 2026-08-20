"""Command-line entry point.

Stage 1: `check-config` reports the loaded config so the domain layer can be
exercised standalone. Stage 2 adds `peer`, a manual round-trip smoke test
for the MCP server/client wiring. Stage 5 adds `tunnel`, which publishes
`my_port` publicly via ngrok so a real opponent team can reach this peer.
Stage 6 adds `declare`, which prints this peer's sealed Step-0
hardware/software declaration. Stage 7 adds `replay`, which steps through a
saved `log_*.json` re-verifying every move's SHA-256 commitment.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from bb_ai_12_police.crypto.commit_reveal import CommitRevealLog
from bb_ai_12_police.crypto.step0 import Step0Declaration
from bb_ai_12_police.domain.barriers import BarrierSet
from bb_ai_12_police.domain.belief import BeliefState
from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.pheromones import PheromoneField
from bb_ai_12_police.gui.replay_viewer import ReplayViewer, load_log
from bb_ai_12_police.llm.resolve_provider import resolve_provider
from bb_ai_12_police.mcp.tunnel import NgrokTunnel
from bb_ai_12_police.runtime.peer_runtime import PeerRuntime
from bb_ai_12_police.shared.config_manager import ConfigManager
from bb_ai_12_police.strategy.resolve_brain import resolve_brain


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bb-ai-12-police")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check-config", help="load config, print grid/port/hash summary")
    check.add_argument("--repo-root", default=".")

    peer = sub.add_parser("peer", help="stage-2 smoke test: send N moves, print replies")
    peer.add_argument("--repo-root", default=".")
    peer.add_argument("--turns", type=int, default=3)

    tunnel = sub.add_parser("tunnel", help="expose my_port publicly via ngrok, print the URL")
    tunnel.add_argument("--repo-root", default=".")

    declare = sub.add_parser("declare", help="print this peer's sealed Step-0 declaration")
    declare.add_argument("--repo-root", default=".")

    replay = sub.add_parser("replay", help="step through a saved log_*.json, verifying SHA-256")
    replay.add_argument("--log", required=True)

    args = parser.parse_args(argv)

    if args.command == "check-config":
        return _check_config(args.repo_root)
    if args.command == "peer":
        return _run_peer(args.repo_root, args.turns)
    if args.command == "tunnel":
        return _run_tunnel(args.repo_root)
    if args.command == "declare":
        return _run_declare(args.repo_root)
    if args.command == "replay":
        return _run_replay(args.log)
    return 1


def _run_peer(repo_root: str, turns: int) -> int:
    cfg = ConfigManager(repo_root)
    shared = cfg.load_shared()
    private = cfg.load_private()
    net = private["network"]

    runtime = PeerRuntime(
        host="127.0.0.1",
        port=net["my_port"],
        opponent_url=net["opponent_url"],
        board=Board.from_config(shared),
        barriers=BarrierSet.from_config(shared),
        belief=BeliefState.from_config(shared, "cop_start", "thief_start"),
        brain=resolve_brain(private),
        trash_talk=resolve_provider(private, shared),
        opponent_scent=PheromoneField.from_config(shared),
        commit_log=CommitRevealLog(),
    )
    runtime.start_server()
    runtime.run_turn_loop(turns)
    return 0


def _run_tunnel(repo_root: str) -> int:
    """Requires the `ngrok` binary installed + authenticated; blocks until Ctrl+C."""
    net = ConfigManager(repo_root).load_private()["network"]
    tunnel = NgrokTunnel(port=net["my_port"])
    public_url = tunnel.start()
    print(f"Public MCP URL: {public_url}/mcp")
    print("Share this with your opponent team as their `opponent_url`. Ctrl+C to stop.")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        tunnel.stop()
    return 0


def _run_declare(repo_root: str) -> int:
    team_code = ConfigManager(repo_root).load_private()["game"]["group_id"]
    declaration = Step0Declaration.create(team_code)
    print(
        json.dumps(
            {
                "payload": declaration.payload,
                "nonce": declaration.nonce,
                "commitment": declaration.commitment,
            },
            indent=2,
        )
    )
    print(f"verify() = {declaration.verify()}")
    return 0


def _run_replay(log_path_str: str) -> int:
    log = load_log(Path(log_path_str))
    viewer = ReplayViewer(log)
    viewer.root.mainloop()
    return 0


def _check_config(repo_root: str) -> int:
    cfg = ConfigManager(repo_root)
    shared = cfg.load_shared()
    private = cfg.load_private()
    board = shared["board_and_agents"]
    print(f"grid_size={board['grid_size']}", end=" ")
    print(f"thief_start={board['thief_start']} cop_start={board['cop_start']}")
    net = private["network"]
    print(f"group_id={private['game']['group_id']} my_port={net['my_port']}")
    print(f"game.json sha256={cfg.game_json_sha256()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
