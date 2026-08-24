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

# Free-tier ngrok tunnels serve a browser-interstitial page instead of the
# real response unless this header is present (any value satisfies it) --
# found live 2026-08-24: it broke the SSE GET that opens a session, so the
# MCP handshake died before negotiate() was ever reached, on the opponent's
# tunnel, not ours -- see docs/TODO.md.
_NGROK_SKIP_WARNING = {"ngrok-skip-browser-warning": "true"}

_CONNECT_ATTEMPTS = 3
_CONNECT_RETRY_DELAY_SEC = 2.0


class LeagueTransport:
    """Wraps one long-lived `Client` connection; use as an async context manager."""

    def __init__(self, opponent_url: str) -> None:
        self.opponent_url = opponent_url
        self._client: Client | None = None

    async def __aenter__(self) -> LeagueTransport:
        transport = StreamableHttpTransport(self.opponent_url, headers=_NGROK_SKIP_WARNING)
        for attempt in range(1, _CONNECT_ATTEMPTS + 1):
            client = Client(transport)
            try:
                await client.__aenter__()
            except Exception:  # noqa: BLE001 - a flaky tunnel/session, retry a few times
                if attempt == _CONNECT_ATTEMPTS:
                    raise
                await asyncio.sleep(_CONNECT_RETRY_DELAY_SEC)
                continue
            self._client = client
            return self
        raise RuntimeError("unreachable")  # pragma: no cover

    async def __aexit__(self, *exc_info: object) -> None:
        if self._client is not None:
            await self._client.__aexit__(*exc_info)
            self._client = None

    async def negotiate(self, message: dict[str, Any]) -> dict[str, Any]:
        result = await self._client.call_tool("negotiate", {"message": message})
        return result.data

    async def send_turn(self, message: dict[str, Any]) -> dict[str, Any]:
        result = await self._client.call_tool("receive_turn", {"message": message})
        return result.data

    async def send_audit(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = await self._client.call_tool("submit_audit", {"payload": payload})
        return result.data

    async def send_control(self, message: dict[str, Any]) -> dict[str, Any]:
        result = await self._client.call_tool("receive_control", {"message": message})
        return result.data
