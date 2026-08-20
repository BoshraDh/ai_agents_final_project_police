"""Outbound MCP client — calls the opponent peer's `receive_move` tool.

Wraps `fastmcp.Client` so the rest of the codebase never touches the raw MCP
session directly; later stages swap the hardcoded move for the real brain's
output without touching this transport code.
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastmcp import Client


class McpTransport:
    """One outbound connection, addressed by the opponent's full MCP URL."""

    def __init__(self, opponent_url: str) -> None:
        self.opponent_url = opponent_url

    async def send_move_async(self, direction: str, turn: int, hint: str = "") -> dict[str, Any]:
        async with Client(self.opponent_url) as client:
            result = await client.call_tool(
                "receive_move", {"direction": direction, "turn": turn, "hint": hint}
            )
        return result.data

    def send_move(self, direction: str, turn: int, hint: str = "") -> dict[str, Any]:
        """Synchronous convenience wrapper around `send_move_async`."""
        return asyncio.run(self.send_move_async(direction, turn, hint))
