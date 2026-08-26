"""Tests for `wait_until_serving` -- the guard against our own 404 startup gap."""

from __future__ import annotations

import httpx

import bb_ai_12_police.league.server_ready as sr


class _Resp:
    def __init__(self, code: int) -> None:
        self.status_code = code


def test_returns_true_once_the_route_stops_answering_404(monkeypatch):
    """Regression test for the defect that killed sub-games 2 and 3 (2026-08-26).

    Uvicorn accepts connections a beat before FastMCP mounts /mcp, so the
    opponent's first receive_turn came back 404 while we looked up. The lost
    turn offsets both step counters by one and the sub-game deadlocks.
    """
    codes = [404, 404, 200]
    calls = {"n": 0}

    def _post(url, **kwargs):
        calls["n"] += 1
        return _Resp(codes.pop(0))

    monkeypatch.setattr(httpx, "post", _post)
    monkeypatch.setattr(sr.time, "sleep", lambda _s: None)
    assert sr.wait_until_serving(8802, timeout_sec=5.0)
    assert calls["n"] == 3


def test_connection_errors_are_treated_as_not_up_yet(monkeypatch):
    attempts = {"n": 0}

    def _post(url, **kwargs):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise httpx.ConnectError("refused")
        return _Resp(200)

    monkeypatch.setattr(httpx, "post", _post)
    monkeypatch.setattr(sr.time, "sleep", lambda _s: None)
    assert sr.wait_until_serving(8802, timeout_sec=5.0)


def test_returns_false_when_the_route_never_mounts(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda url, **k: _Resp(404))
    monkeypatch.setattr(sr.time, "sleep", lambda _s: None)
    assert not sr.wait_until_serving(8802, timeout_sec=0.05)
