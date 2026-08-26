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

    def fake_run(repo_root, turns, opponent_url, sub_game, friendly, report_to, game_id=None):
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

    def fake_run(repo_root, turns, opponent_url, sub_game, friendly, report_to, game_id=None):
        captured["friendly"] = friendly
        return 0

    monkeypatch.setattr("bb_ai_12_police.cli.league_peer.run", fake_run)
    main(["league-peer", "--sub-game", "1"])
    assert captured["friendly"] is False


def test_league_peer_wires_report_to_through(monkeypatch):
    captured = {}

    def fake_run(repo_root, turns, opponent_url, sub_game, friendly, report_to, game_id=None):
        captured["report_to"] = report_to
        return 0

    monkeypatch.setattr("bb_ai_12_police.cli.league_peer.run", fake_run)
    main(["league-peer", "--sub-game", "1", "--report-to", "a@x.com,b@y.com"])
    assert captured["report_to"] == "a@x.com,b@y.com"


def test_league_peer_wires_the_match_level_game_id_through(monkeypatch):
    # One game_id per MATCH: the book derives every artifact filename from it
    # plus the sub-game number "so that files from different games are never
    # mixed". Before this, each sub-game minted its own random id.
    captured = {}

    def fake_run(repo_root, turns, opponent_url, sub_game, friendly, report_to, game_id=None):
        captured["game_id"] = game_id
        return 0

    monkeypatch.setattr("bb_ai_12_police.cli.league_peer.run", fake_run)
    main(["league-peer", "--sub-game", "3", "--game-id", "SMNGRP05-vs-bb-ai-12"])
    assert captured["game_id"] == "SMNGRP05-vs-bb-ai-12"


def test_league_peer_game_id_defaults_to_none(monkeypatch):
    captured = {}

    def fake_run(repo_root, turns, opponent_url, sub_game, friendly, report_to, game_id=None):
        captured["game_id"] = game_id
        return 0

    monkeypatch.setattr("bb_ai_12_police.cli.league_peer.run", fake_run)
    main(["league-peer", "--sub-game", "1"])
    assert captured["game_id"] is None
