"""Tests for the 4 inbound league tools registered on a FastMCP instance."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP

from bb_ai_12_police.league.inbox import LeagueInbox
from bb_ai_12_police.league.server_tools import add_league_tools


def _tools(mcp: FastMCP) -> dict:
    async def _fetch():
        names = ["negotiate", "receive_turn", "submit_audit", "receive_control"]
        return {name: (await mcp.get_tool(name)).fn for name in names}

    return asyncio.run(_fetch())


def test_negotiate_stores_the_message_and_replies_with_the_given_reply():
    inbox = LeagueInbox()
    mcp = FastMCP(name="test")
    add_league_tools(mcp, inbox, {"status": "accepted", "nonce": "abc"})
    tools = _tools(mcp)
    reply = tools["negotiate"]({"terms": {"a": 1}})
    assert reply == {"status": "accepted", "nonce": "abc"}
    assert inbox.wait_for_negotiate(1, 0.05) == {"terms": {"a": 1}}


def test_receive_turn_stores_the_message_by_step():
    inbox = LeagueInbox()
    mcp = FastMCP(name="test")
    add_league_tools(mcp, inbox, {"status": "accepted"})
    tools = _tools(mcp)
    tools["receive_turn"]({"step": 5, "hint": "hi"})
    assert inbox.wait_for_turn(5, timeout_sec=1.0)["hint"] == "hi"


def test_submit_audit_stores_the_payload():
    inbox = LeagueInbox()
    mcp = FastMCP(name="test")
    add_league_tools(mcp, inbox, {"status": "accepted"})
    tools = _tools(mcp)
    tools["submit_audit"]({"sender": "police"})
    assert inbox.audit == {"sender": "police"}


def test_receive_control_just_acks():
    inbox = LeagueInbox()
    mcp = FastMCP(name="test")
    add_league_tools(mcp, inbox, {"status": "accepted"})
    tools = _tools(mcp)
    assert tools["receive_control"]({"kind": "status"}) == {"ok": True}
