"""Command-line entry point.

Stage 1 (current): only reports the loaded config so the domain layer can be
exercised standalone. `peer`/`replay` subcommands are added in later stages
once MCP networking (stage 2) and the crypto/report layers exist.
"""

from __future__ import annotations

import argparse
import sys

from bb_ai_12_police.shared.config_manager import ConfigManager


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bb-ai-12-police")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check-config", help="load config, print grid/port/hash summary")
    check.add_argument("--repo-root", default=".")

    args = parser.parse_args(argv)

    if args.command == "check-config":
        return _check_config(args.repo_root)
    return 1


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
