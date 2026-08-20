"""Command-line entry point.

Stage 1: `check-config` reports the loaded config so the domain layer can be
exercised standalone. Stage 2 adds `peer`, a manual round-trip smoke test
for the MCP server/client wiring — the `replay` subcommand arrives once the
crypto/report layers exist (stage 6-7).
"""

from __future__ import annotations

import argparse
import sys

from bb_ai_12_police.runtime.peer_runtime import PeerRuntime
from bb_ai_12_police.shared.config_manager import ConfigManager


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bb-ai-12-police")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check-config", help="load config, print grid/port/hash summary")
    check.add_argument("--repo-root", default=".")

    peer = sub.add_parser("peer", help="stage-2 smoke test: send N moves, print replies")
    peer.add_argument("--repo-root", default=".")
    peer.add_argument("--turns", type=int, default=3)

    args = parser.parse_args(argv)

    if args.command == "check-config":
        return _check_config(args.repo_root)
    if args.command == "peer":
        return _run_peer(args.repo_root, args.turns)
    return 1


def _run_peer(repo_root: str, turns: int) -> int:
    private = ConfigManager(repo_root).load_private()
    net = private["network"]
    runtime = PeerRuntime(host="127.0.0.1", port=net["my_port"], opponent_url=net["opponent_url"])
    runtime.start_server()
    runtime.run_turn_loop(turns)
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
