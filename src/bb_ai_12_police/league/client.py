"""Outbound calls to an opponent running the league kit's 4-tool server.

Unlike `mcp/client.py`'s `McpTransport` (a fresh connection per call), this
opens ONE `fastmcp.Client` session for the whole sub-game and reuses it —
the kit's own spec flags per-call sessions as what trips a free-tier
tunnel's rate limit at scale.
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from bb_ai_12_police.league.wire_log import note, trace

# Free-tier ngrok tunnels serve a browser-interstitial page instead of the
# real response unless this header is present (any value satisfies it) --
# found live 2026-08-24: it broke the SSE GET that opens a session, so the
# MCP handshake died before negotiate() was ever reached, on the opponent's
# tunnel, not ours -- see docs/TODO.md.
_NGROK_SKIP_WARNING = {"ngrok-skip-browser-warning": "true"}

# The FIRST connect happens while the opponent may not have started their peer
# yet -- the agreed coordination with SMNGRP05 is "we go up first, then tell
# them", so ~6s of retries meant our process died before they ever dialled.
# 45 x 4s = 180s, matching `handshake_timeout_sec`. A LATER reconnect is a
# different case (the opponent is known to be up, a session just dropped), so
# it stays short: blocking 180s mid-game would blow past their turn watchdog.
_CONNECT_ATTEMPTS = 45
_CONNECT_RETRY_DELAY_SEC = 4.0
_RECONNECT_ATTEMPTS = 3
_RECONNECT_RETRY_DELAY_SEC = 2.0


class LeagueTransport:
    """Wraps one long-lived `Client` connection; use as an async context manager."""

    def __init__(self, opponent_url: str) -> None:
        self.opponent_url = opponent_url
        self._client: Client | None = None
        self._connected_once = False

    async def __aenter__(self) -> LeagueTransport:
        transport = StreamableHttpTransport(self.opponent_url, headers=_NGROK_SKIP_WARNING)
        if self._connected_once:
            attempts, delay = _RECONNECT_ATTEMPTS, _RECONNECT_RETRY_DELAY_SEC
        else:
            attempts, delay = _CONNECT_ATTEMPTS, _CONNECT_RETRY_DELAY_SEC
        for attempt in range(1, attempts + 1):
            client = Client(transport)
            try:
                await client.__aenter__()
            except Exception:  # noqa: BLE001 - a flaky tunnel/session, retry a few times
                if attempt == attempts:
                    raise
                await asyncio.sleep(delay)
                continue
            self._client = client
            self._connected_once = True
            return self
        raise RuntimeError("unreachable")  # pragma: no cover

    async def __aexit__(self, *exc_info: object) -> None:
        if self._client is not None:
            await self._client.__aexit__(*exc_info)
            self._client = None

    async def _reconnect(self) -> None:
        if self._client is not None:
            try:
                await self._client.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001 - the old session is already dead
                pass
            self._client = None
        await self.__aenter__()

    async def _call(self, tool: str, arg_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        # An opponent's server can terminate the underlying session between
        # calls (found live 2026-08-26 vs SMNGRP05: negotiate succeeded, then
        # sending turn 1 raised McpError("Session terminated")) -- reconnect
        # once and retry instead of failing the whole sub-game outright.
        #
        # This retry used to be entirely silent, which was a real blind spot:
        # a reconnect opens a BRAND-NEW MCP session, so a call that succeeds on
        # the retry can land somewhere different from where the earlier calls
        # in this sub-game went, and we would log only the success. Trace it.
        trace("OUT", tool, payload)
        try:
            result = await self._client.call_tool(tool, {arg_name: payload})
        except Exception as exc:  # noqa: BLE001 - reconnect and retry once
            note(f"{tool} raised {exc!r}; reconnecting (NEW session) and retrying once")
            await self._reconnect()
            try:
                result = await self._client.call_tool(tool, {arg_name: payload})
            except Exception as retry_exc:  # noqa: BLE001 - traced, then propagated
                trace("OUT-ERR", tool, payload, detail=f"error={retry_exc!r}")
                raise
            note(f"{tool} succeeded on the retry, on a different session")
        reply = result.structured_content or result.data
        # The reply is traced in the SAME stream as the send, with the same
        # tool/step/commit identity, so a diff against the opponent's inbound
        # list can tell "we sent and they answered" apart from "we sent and it
        # never landed" without cross-referencing a second log.
        trace("OUT-OK", tool, payload, detail=f"reply={reply!r}")
        return reply

    async def negotiate(self, message: dict[str, Any]) -> dict[str, Any]:
        return await self._call("negotiate", "message", message)

    async def send_turn(self, message: dict[str, Any]) -> dict[str, Any]:
        return await self._call("receive_turn", "message", message)

    async def send_audit(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._call("submit_audit", "payload", payload)

    async def send_control(self, message: dict[str, Any]) -> dict[str, Any]:
        return await self._call("receive_control", "message", message)
