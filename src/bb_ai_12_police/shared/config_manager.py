"""Loads and merges the two-file config split (book Appendix ב).

`game.json`  — SHARED, signed, must be byte-identical between both peers'
               repos. Holds only terms both sides must agree on.
`game.toml`  — PRIVATE, this peer's own business only (port, opponent URL,
               team identity, strategy/LLM choice, email). Never leaks into
               the shared agreement.

`load()` returns a single merged mapping so the rest of the codebase reads
one object instead of two files, while `game_json_sha256()` lets the crypto
layer verify the shared file wasn't tampered with independently of the
merge.
"""

from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path
from typing import Any


class ConfigManager:
    """Reads `config/game.json` + `config/game.toml` from a repo root."""

    def __init__(self, repo_root: Path | str = ".") -> None:
        self.repo_root = Path(repo_root)
        self.game_json_path = self.repo_root / "config" / "game.json"
        self.game_toml_path = self.repo_root / "config" / "game.toml"

    def load_shared(self) -> dict[str, Any]:
        """The signed, must-match-the-opponent terms."""
        with self.game_json_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def load_private(self) -> dict[str, Any]:
        """This peer's own local-only settings."""
        with self.game_toml_path.open("rb") as f:
            return tomllib.load(f)

    def load(self) -> dict[str, Any]:
        """Merged view: shared terms plus a `_private` sub-key for local-only data.

        Kept as two distinct top-level regions (rather than flattened) so
        callers can never accidentally write a private value where a shared,
        signed one is expected.
        """
        merged = self.load_shared()
        merged["_private"] = self.load_private()
        return merged

    def game_json_sha256(self) -> str:
        """Canonical-form hash of the raw shared file, for pre-game verification.

        Uses the raw file bytes (not a re-serialized form) so this matches
        exactly what `git diff`/`sha256sum` on the file itself would report —
        the two peers compare this value directly during the handshake.
        """
        raw = self.game_json_path.read_bytes()
        return hashlib.sha256(raw).hexdigest()
