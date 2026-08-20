"""Tests for the Gmail message builder and send wrapper — no real Gmail call.

`send_report`'s `service_factory` is always a fake here, so these tests
never touch real Google credentials or the network.
"""

from __future__ import annotations

import base64
from email import policy
from email.parser import BytesParser

from bb_ai_12_police.infra.email_sender import build_message, send_report


def test_build_message_encodes_recipient_subject_and_body(tmp_path):
    attachment = tmp_path / "result_g1.json"
    attachment.write_text('{"a": 1}', encoding="utf-8")

    raw = build_message("grader@example.com", "Report", "See attached.", [attachment])["raw"]
    decoded = BytesParser(policy=policy.default).parsebytes(base64.urlsafe_b64decode(raw))

    assert decoded["To"] == "grader@example.com"
    assert decoded["Subject"] == "Report"
    attachments = [part for part in decoded.iter_attachments()]
    assert len(attachments) == 1
    assert attachments[0].get_filename() == "result_g1.json"


class _FakeSend:
    def __init__(self, captured: dict) -> None:
        self._captured = captured

    def execute(self) -> dict:
        return {"id": "fake-message-id"}


class _FakeMessages:
    def __init__(self, captured: dict) -> None:
        self._captured = captured

    def send(self, userId: str, body: dict) -> _FakeSend:
        self._captured["userId"] = userId
        self._captured["body"] = body
        return _FakeSend(self._captured)


class _FakeUsers:
    def __init__(self, captured: dict) -> None:
        self._captured = captured

    def messages(self) -> _FakeMessages:
        return _FakeMessages(self._captured)


class _FakeService:
    def __init__(self, captured: dict) -> None:
        self._captured = captured

    def users(self) -> _FakeUsers:
        return _FakeUsers(self._captured)


def test_send_report_calls_the_gmail_service_and_returns_its_response(tmp_path):
    attachment = tmp_path / "result_g1.json"
    attachment.write_text("{}", encoding="utf-8")
    captured: dict = {}

    result = send_report(
        token_path=tmp_path / "token.json",
        recipient="grader@example.com",
        subject="Report",
        body="See attached.",
        attachments=[attachment],
        service_factory=lambda token_path: _FakeService(captured),
    )

    assert result == {"id": "fake-message-id"}
    assert captured["userId"] == "me"
    assert "raw" in captured["body"]
