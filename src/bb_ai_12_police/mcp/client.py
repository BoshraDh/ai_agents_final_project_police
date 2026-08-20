"""Outbound MCP client — calls the opponent peer's turn-protocol tools.

Wraps `fastmcp.Client` so the rest of the codebase never touches the raw MCP
session directly.
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastmcp import Client


class McpTransport:
    """One outbound connection, addressed by the opponent's full MCP URL."""

    def __init__(self, opponent_url: str) -> None:
        self.opponent_url = opponent_url

    async def send_commit_async(self, h_commit: str, turn: int) -> dict[str, Any]:
        async with Client(self.opponent_url) as client:
            result = await client.call_tool("submit_commit", {"h_commit": h_commit, "turn": turn})
        return result.data

    def send_commit(self, h_commit: str, turn: int) -> dict[str, Any]:
        return asyncio.run(self.send_commit_async(h_commit, turn))

    async def send_reveal_async(
        self, move: str, hint: str, intent: str, turn: int
    ) -> dict[str, Any]:
        async with Client(self.opponent_url) as client:
            result = await client.call_tool(
                "submit_reveal", {"move": move, "hint": hint, "intent": intent, "turn": turn}
            )
        return result.data

    def send_reveal(self, move: str, hint: str, intent: str, turn: int) -> dict[str, Any]:
        return asyncio.run(self.send_reveal_async(move, hint, intent, turn))
