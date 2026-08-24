"""Tests for the build -> write -> email orchestration (no real Gmail call)."""

from __future__ import annotations

import logging

from bb_ai_12_police.crypto.commit_reveal import CommitRevealLog
from bb_ai_12_police.crypto.step0 import Step0Declaration
from bb_ai_12_police.domain.protocol import GameOutcome, Role
from bb_ai_12_police.report.emit import emit_report

_SHARED_CONFIG = {
    "rate_limiter_gatekeeper": {
        "requests_per_minute": 30,
        "concurrent_requests": 2,
        "retry_backoff_sec": 5,
        "max_retries": 3,
        "queue_depth": 100,
    }
}


def _commit_log() -> CommitRevealLog:
    log = CommitRevealLog()
    log.seal(1, {"move": "N"})
    return log


def test_emit_report_writes_artifacts_and_sends_email(tmp_path, monkeypatch):
    captured: dict = {}

    def fake_send_report(token_path, recipient, subject, body, attachments):
        captured["token_path"] = token_path
        captured["recipient"] = recipient
        captured["subject"] = subject
        captured["attachments"] = attachments
        return {"id": "fake-message-id"}

    monkeypatch.setattr("bb_ai_12_police.report.emit.send_report", fake_send_report)

    response = emit_report(
        logs_dir=tmp_path / "logs",
        group_id="bb-ai-12",
        sub_game_number=1,
        outcome=GameOutcome.CAPTURED,
        role=Role.POLICE,
        commit_log=_commit_log(),
        step0=Step0Declaration.create("bb-ai-12"),
        shared_config=_SHARED_CONFIG,
        game_json_sha256="deadbeef",
        recipient="grader@example.com",
        token_path=tmp_path / "token.json",
    )

    assert response == {"id": "fake-message-id"}
    assert captured["recipient"] == "grader@example.com"
    assert "captured" in captured["subject"]
    assert len(captured["attachments"]) == 4
    for path in captured["attachments"]:
        assert path.exists()


def test_emit_report_returns_none_and_logs_when_send_fails(tmp_path, monkeypatch, caplog):
    def boom(token_path, recipient, subject, body, attachments):
        raise RuntimeError("gmail is down")

    monkeypatch.setattr("bb_ai_12_police.report.emit.send_report", boom)

    with caplog.at_level(logging.ERROR):
        response = emit_report(
            logs_dir=tmp_path / "logs",
            group_id="bb-ai-12",
            sub_game_number=1,
            outcome=GameOutcome.SURVIVED,
            role=Role.THIEF,
            commit_log=_commit_log(),
            step0=Step0Declaration.create("bb-ai-12"),
            shared_config=_SHARED_CONFIG,
            game_json_sha256="deadbeef",
            recipient="grader@example.com",
            token_path=tmp_path / "token.json",
        )

    assert response is None
    assert "send_report failed" in caplog.text
    # The artifacts must still be on disk even though the send failed.
    written = list((tmp_path / "logs" / "bb-ai-12").glob("*.json"))
    assert len(written) == 4
