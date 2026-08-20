"""Tests for the outbound MCP client, against an in-process FastMCP server.

`fastmcp.Client` accepts a `FastMCP` instance directly (in-memory transport,
no real socket) — used here so the round trip is verified without binding a
port, matching fastmcp's own recommended testing pattern.
"""

from __future__ import annotations

from bb_ai_12_police.mcp.client import McpTransport
from bb_ai_12_police.mcp.server import mcp


def test_send_move_round_trips_in_process():
    transport = McpTransport(mcp)
    reply = transport.send_move("N", 1)
    assert reply == {"direction": "STAY", "turn": 1}


def test_send_move_exercises_the_async_path_via_asyncio_run():
    transport = McpTransport(mcp)
    reply = transport.send_move("E", 3)
    assert reply == {"direction": "STAY", "turn": 3}
