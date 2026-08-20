"""Pre-game agreement check (book Appendix ב's shared-config requirement).

Both peers must be using byte-identical `config/game.json` before a match
starts — verified here via SHA-256 comparison (`ConfigManager.
game_json_sha256()` on each side). This is deliberately just the
agreement *check*, not a full negotiation handshake (assigning a game_id,
deciding who moves first, etc.) — that sequencing needs the book's exact
protocol re-confirmed before being built; see `docs/TODO.md`.
"""

from __future__ import annotations


def configs_match(local_sha256: str, remote_sha256: str) -> bool:
    return local_sha256 == remote_sha256
