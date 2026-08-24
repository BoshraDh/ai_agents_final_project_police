"""Command-line entry point: argparse setup, dispatching to one module per
subcommand (`cli/check_config.py`, `cli/peer.py`, `cli/tunnel.py`,
`cli/declare.py`, `cli/replay.py`) so no single file needs to grow past the
150-line cap as more subcommands are added.
"""

from __future__ import annotations

import argparse
import sys

from bb_ai_12_police.cli import check_config, declare, league_peer, peer, replay, tunnel


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bb-ai-12-police")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check-config", help="load config, print grid/port/hash summary")
    check.add_argument("--repo-root", default=".")

    peer_p = sub.add_parser("peer", help="play real rounds against the opponent")
    peer_p.add_argument("--repo-root", default=".")
    peer_p.add_argument("--turns", type=int, default=3)

    tunnel_p = sub.add_parser("tunnel", help="expose my_port publicly via ngrok, print the URL")
    tunnel_p.add_argument("--repo-root", default=".")

    declare_p = sub.add_parser("declare", help="print this peer's sealed Step-0 declaration")
    declare_p.add_argument("--repo-root", default=".")

    replay_p = sub.add_parser("replay", help="step through a saved log_*.json, verify SHA-256")
    replay_p.add_argument("--log", required=True)

    league_p = sub.add_parser("league-peer", help="play one sub-game over the league kit's wire")
    league_p.add_argument("--repo-root", default=".")
    league_p.add_argument("--turns", type=int, default=35)
    league_p.add_argument("--opponent-url", default=None)
    league_p.add_argument("--sub-game", type=int, default=None)
    league_p.add_argument(
        "--friendly",
        action="store_true",
        help="uncounted practice game: skip the automatic end-of-game report email",
    )

    args = parser.parse_args(argv)

    if args.command == "check-config":
        return check_config.run(args.repo_root)
    if args.command == "peer":
        return peer.run(args.repo_root, args.turns)
    if args.command == "tunnel":
        return tunnel.run(args.repo_root)
    if args.command == "declare":
        return declare.run(args.repo_root)
    if args.command == "replay":
        return replay.run(args.log)
    if args.command == "league-peer":
        return league_peer.run(
            args.repo_root, args.turns, args.opponent_url, args.sub_game, args.friendly
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
