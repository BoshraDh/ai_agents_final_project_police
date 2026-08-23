"""Outbound calls to an opponent running the league kit's 4-tool server.

Unlike `mcp/client.py`'s `McpTransport` (a fresh connection per call), this
opens ONE `fastmcp.Client` session for the whole sub-game and reuses it —
the kit's own spec flags per-call sessions as what trips a free-tier
tunnel's rate limit at scale.
"""

from __future__ import annotations

from typing import Any

from fastmcp import Client


class LeagueTransport:
    """Wraps one long-lived `Client` connection; use as an async context manager."""

    def __init__(self, opponent_url: str) -> None:
        self.opponent_url = opponent_url
        self._client: Client | None = None

    async def __aenter__(self) -> LeagueTransport:
        self._client = Client(self.opponent_url)
        await self._client.__aenter__()
        return self

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
