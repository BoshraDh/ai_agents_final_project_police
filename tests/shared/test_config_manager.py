from pathlib import Path

from bb_ai_12_police.shared.config_manager import ConfigManager

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_load_shared_has_binding_defaults():
    cfg = ConfigManager(REPO_ROOT)
    shared = cfg.load_shared()
    assert shared["board_and_agents"]["grid_size"] == 7
    assert shared["scoring"]["capture_cop"] == 20
    assert shared["pheromones"]["pheromone_decay"] == 0.10


def test_load_private_has_this_peers_settings():
    cfg = ConfigManager(REPO_ROOT)
    private = cfg.load_private()
    assert private["game"]["group_id"] == "bb-ai-12"
    assert private["network"]["my_port"] == 8802


def test_merged_load_nests_private_under_key():
    cfg = ConfigManager(REPO_ROOT)
    merged = cfg.load()
    assert "_private" in merged
    assert merged["_private"]["network"]["my_port"] == 8802
    assert merged["board_and_agents"]["grid_size"] == 7


def test_game_json_sha256_is_stable_and_hex():
    cfg = ConfigManager(REPO_ROOT)
    h1 = cfg.game_json_sha256()
    h2 = cfg.game_json_sha256()
    assert h1 == h2
    assert len(h1) == 64
    int(h1, 16)  # raises ValueError if not valid hex
