"""`replay` — step through a saved log_*.json, verifying SHA-256."""

from __future__ import annotations

from pathlib import Path

from bb_ai_12_police.gui.replay_viewer import ReplayViewer, load_log


def run(log_path_str: str) -> int:
    log = load_log(Path(log_path_str))
    viewer = ReplayViewer(log)
    viewer.root.mainloop()
    return 0
