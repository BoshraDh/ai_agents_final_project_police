from pathlib import Path

from bb_ai_12_police.cli import main

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_check_config_runs_cleanly(capsys):
    exit_code = main(["check-config", "--repo-root", str(REPO_ROOT)])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "grid_size=7" in out
    assert "my_port=8802" in out
    assert "sha256=" in out
