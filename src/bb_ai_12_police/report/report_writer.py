"""Writes the four mandatory artifacts to `logs/<group_id>/`."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bb_ai_12_police.domain.game_ids import artifact_filename


def write_artifacts(
    logs_dir: Path,
    group_id: str,
    game_id: str,
    sub_game_number: int,
    declaration: dict[str, Any],
    config: dict[str, Any],
    log: dict[str, Any],
    result: dict[str, Any],
) -> list[Path]:
    """Writes all four files; returns their paths (for the email attachments)."""
    target_dir = logs_dir / group_id
    target_dir.mkdir(parents=True, exist_ok=True)

    written = []
    for kind, payload in (
        ("declaration", declaration),
        ("config", config),
        ("log", log),
        ("result", result),
    ):
        path = target_dir / artifact_filename(kind, game_id, sub_game_number)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        written.append(path)
    return written
