"""Game/sub-game identifiers used in the four mandatory report filenames.

Real game_id assignment likely belongs to the negotiation handshake this
repo has deferred since stage 3 (see `docs/PRD_strategy.md`) — this is a
placeholder scheme (`<team_code>_<8 random hex chars>`) good enough to
produce a unique, filesystem-safe id for local testing and the report
artifacts, pending the book's exact format being re-confirmed.
"""

from __future__ import annotations

import secrets


def generate_game_id(team_code: str) -> str:
    return f"{team_code}_{secrets.token_hex(4)}"


def artifact_filename(kind: str, game_id: str, sub_game_number: int | None = None) -> str:
    """`kind` is one of "declaration", "config", "log", "result"."""
    if kind == "declaration" or kind == "result":
        return f"{kind}_{game_id}.json"
    return f"{kind}_{game_id}_g{sub_game_number:02d}.json"
