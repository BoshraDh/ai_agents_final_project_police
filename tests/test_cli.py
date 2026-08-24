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


def test_league_peer_wires_the_friendly_flag_through(monkeypatch):
    captured = {}

    def fake_run(repo_root, turns, opponent_url, sub_game, friendly, report_to):
        captured["friendly"] = friendly
        captured["report_to"] = report_to
        return 0

    monkeypatch.setattr("bb_ai_12_police.cli.league_peer.run", fake_run)
    exit_code = main(["league-peer", "--sub-game", "1", "--friendly"])
    assert exit_code == 0
    assert captured["friendly"] is True
    assert captured["report_to"] is None


def test_league_peer_defaults_friendly_to_false(monkeypatch):
    captured = {}

    def fake_run(repo_root, turns, opponent_url, sub_game, friendly, report_to):
        captured["friendly"] = friendly
        return 0

    monkeypatch.setattr("bb_ai_12_police.cli.league_peer.run", fake_run)
    main(["league-peer", "--sub-game", "1"])
    assert captured["friendly"] is False


def test_league_peer_wires_report_to_through(monkeypatch):
    captured = {}

    def fake_run(repo_root, turns, opponent_url, sub_game, friendly, report_to):
        captured["report_to"] = report_to
        return 0

    monkeypatch.setattr("bb_ai_12_police.cli.league_peer.run", fake_run)
    main(["league-peer", "--sub-game", "1", "--report-to", "a@x.com,b@y.com"])
    assert captured["report_to"] == "a@x.com,b@y.com"
