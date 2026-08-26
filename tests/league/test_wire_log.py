"""The wire log is the agreed instrument for settling an inbound/outbound
dispute with an opponent (see `league/wire_log.py`), so its line shape and the
OUT/OUT-OK pairing are asserted here rather than trusted.
"""

from __future__ import annotations

import asyncio

import pytest

from bb_ai_12_police.league.client import LeagueTransport
from bb_ai_12_police.league.wire_log import trace


class _Result:
    def __init__(self, payload: dict) -> None:
        self.structured_content = payload
        self.data = payload


class _FakeClient:
    """Stands in for `fastmcp.Client`, recording every call it is handed."""

    def __init__(self, *, fail_times: int = 0) -> None:
        self.calls: list[tuple[str, dict]] = []
        self._fail_times = fail_times

    async def call_tool(self, tool: str, args: dict) -> _Result:
        self.calls.append((tool, args))
        if self._fail_times > 0:
            self._fail_times -= 1
            raise RuntimeError("Session terminated")
        return _Result({"ok": True})


def _wire_lines(capsys) -> list[str]:
    out = capsys.readouterr().out
    return [ln for ln in out.splitlines() if ln.startswith("[wire] ")]


def test_trace_carries_step_sub_game_and_commit_prefix(capsys) -> None:
    trace("IN", "receive_turn", {"step": 4, "sub_game_number": 2, "commit": "a" * 64})
    (line,) = _wire_lines(capsys)
    assert " IN " in line
    assert "receive_turn" in line
    assert "step=4" in line
    assert "sub_game=2" in line
    assert f"commit={'a' * 12}" in line
    assert "a" * 13 not in line


def test_trace_appends_detail_verbatim(capsys) -> None:
    trace("OUT-OK", "receive_turn", {"step": 1}, detail="reply={'ok': True}")
    (line,) = _wire_lines(capsys)
    assert line.endswith("reply={'ok': True}")


def test_successful_call_traces_the_reply_not_just_the_send(capsys) -> None:
    # The bug this guards: `OUT` is printed BEFORE the call, so without a
    # matching `OUT-OK` a call that never completed is indistinguishable from
    # one the opponent answered -- the exact ambiguity the log must remove.
    transport = LeagueTransport("http://opponent.invalid/mcp")
    transport._client = _FakeClient()  # noqa: SLF001 - no live opponent in tests

    reply = asyncio.run(transport.send_turn({"step": 7, "commit": "b" * 64}))

    assert reply == {"ok": True}
    sent, returned = _wire_lines(capsys)
    assert " OUT " in sent
    assert "reply=" not in sent
    assert " OUT-OK " in returned
    assert "step=7" in returned
    assert "reply={'ok': True}" in returned


def test_failed_call_traces_out_err_and_propagates(capsys, monkeypatch) -> None:
    transport = LeagueTransport("http://opponent.invalid/mcp")
    transport._client = _FakeClient(fail_times=2)  # noqa: SLF001 - see above

    async def _no_reconnect() -> None:
        return None

    monkeypatch.setattr(transport, "_reconnect", _no_reconnect)

    with pytest.raises(RuntimeError):
        asyncio.run(transport.send_turn({"step": 3, "commit": "c" * 64}))

    lines = _wire_lines(capsys)
    assert any(" OUT " in ln for ln in lines)
    assert not any(" OUT-OK " in ln for ln in lines)
    errors = [ln for ln in lines if " OUT-ERR " in ln]
    assert len(errors) == 1
    assert "step=3" in errors[0]
    assert "Session terminated" in errors[0]
