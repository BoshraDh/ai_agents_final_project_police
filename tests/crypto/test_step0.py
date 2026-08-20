"""Tests for the Step-0 sealed hardware/software declaration."""

from __future__ import annotations

from bb_ai_12_police.crypto.step0 import Step0Declaration


def test_create_includes_the_team_code_and_sysinfo_fields():
    declaration = Step0Declaration.create("bb-ai-12")
    assert declaration.payload["team_code"] == "bb-ai-12"
    assert "python_version" in declaration.payload
    assert "platform" in declaration.payload


def test_verify_succeeds_for_an_untouched_declaration():
    declaration = Step0Declaration.create("bb-ai-12")
    assert declaration.verify()


def test_verify_fails_if_the_payload_is_tampered_with():
    declaration = Step0Declaration.create("bb-ai-12")
    declaration.payload["team_code"] = "someone-else"
    assert not declaration.verify()
