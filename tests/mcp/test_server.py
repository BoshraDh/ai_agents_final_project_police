"""Tests for the inbound submit_commit/submit_reveal turn-protocol tools."""

from __future__ import annotations

import asyncio

import pytest

from bb_ai_12_police.mcp.server import build_server
from bb_ai_12_police.peer.turn_handler import TurnHandler


def _tools(mcp):
    """Fetch the underlying Python functions FastMCP registered as tools."""

    async def _fetch():
        return {
            "submit_commit": (await mcp.get_tool("submit_commit")).fn,
            "submit_reveal": (await mcp.get_tool("submit_reveal")).fn,
        }

    return asyncio.run(_fetch())


def test_submit_commit_records_it_on_the_shared_turn_handler():
    handler = TurnHandler()
    tools = _tools(build_server("test", handler))
    reply = tools["submit_commit"]("deadbeef", 1)
    assert reply == {"received": True, "turn": 1}
    assert handler.has_received_commit(1)


def test_submit_reveal_returns_our_own_prepared_reveal():
    handler = TurnHandler()
    handler.receive_commit(1, "deadbeef")
    handler.prepare_own_reveal(1, "N", "your move, criminal", "truth")
    tools = _tools(build_server("test", handler))
    reply = tools["submit_reveal"]("S", "never", "lie", 1)
    assert reply == {"move": "N", "hint": "your move, criminal", "intent": "truth", "turn": 1}


def test_submit_reveal_raises_without_a_prior_commit():
    handler = TurnHandler()
    tools = _tools(build_server("test", handler))
    with pytest.raises(ValueError, match="protocol violation"):
        tools["submit_reveal"]("S", "never", "lie", 1)
