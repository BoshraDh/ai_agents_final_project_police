"""`check-config` — load config, print grid/port/hash summary."""

from __future__ import annotations

from bb_ai_12_police.shared.config_manager import ConfigManager


def run(repo_root: str) -> int:
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
