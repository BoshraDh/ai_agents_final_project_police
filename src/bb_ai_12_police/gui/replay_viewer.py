"""Replay Viewer: step through a saved `log_*.json`, re-verifying every
move's SHA-256 commitment and showing "Verified OK" / "TAMPERED".

Reuses `crypto.commit_reveal.verify_reveal` directly against the log
file's own recorded (payload, nonce, commitment) triples — the same audit
`CommitRevealLog.audit()` performs in-memory, applied here to data loaded
back from disk (the book's replay/audit requirement).
"""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from typing import Any

from bb_ai_12_police.crypto.commit_reveal import verify_reveal


def load_log(log_path: Path) -> dict[str, Any]:
    return json.loads(log_path.read_text(encoding="utf-8"))


def verify_move(move: dict[str, Any]) -> bool:
    return verify_reveal(move["payload"], move["nonce"], move["commitment"])


class ReplayViewer:
    """Step-through viewer over one loaded log's `moves` list."""

    def __init__(self, log: dict[str, Any], show: bool = True) -> None:
        self.moves = log["moves"]
        self.index = 0
        self.root = tk.Tk()
        self.root.title(f"bb-ai-12 — replay {log['game_id']} g{log['sub_game_number']:02d}")
        if not show:
            self.root.withdraw()
        self.label = tk.Label(self.root, text="", anchor="w")
        self.label.pack(fill="x")
        tk.Button(self.root, text="Next", command=self.next_move).pack()
        self._render()

    def next_move(self) -> None:
        if self.index < len(self.moves) - 1:
            self.index += 1
            self._render()

    def _render(self) -> None:
        if not self.moves:
            self.label.config(text="(empty log)")
            return
        move = self.moves[self.index]
        status = "Verified OK" if verify_move(move) else "TAMPERED"
        self.label.config(text=f"Turn {move['turn']}: {move['payload']} — {status}")
        self.root.update()

    def close(self) -> None:
        self.root.destroy()
