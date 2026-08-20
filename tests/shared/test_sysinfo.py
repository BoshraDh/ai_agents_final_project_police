"""Tests for the Step-0 environment collector."""

from __future__ import annotations

from bb_ai_12_police.shared.sysinfo import collect_sysinfo


def test_collect_sysinfo_returns_the_expected_keys():
    info = collect_sysinfo()
    assert set(info) == {"python_version", "platform", "processor", "machine"}
    assert all(isinstance(v, str) and v for v in info.values())
