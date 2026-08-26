"""Registers the league kit's 4 inbound tools on an existing FastMCP
instance, alongside (not replacing) `mcp/server.py`'s own
`submit_commit`/`submit_reveal`. Every handler just hands the message to
the `LeagueInbox` for the (separate-thread) game loop to consume — no
game logic lives here, matching `mcp/server.py`'s own thin-handler style.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from bb_ai_12_police.league.inbox import LeagueInbox
from bb_ai_12_police.league.wire_log import trace


def add_league_tools(
    mcp: FastMCP, inbox: LeagueInbox, negotiate_reply: dict[str, Any]
) -> None:
    # An opponent that omits `sub_game_number` is filed under the sub-game this
    # process is actually playing, which `negotiate_reply` already carries.
    own_sub_game = negotiate_reply.get("sub_game_number", 1)

    @mcp.tool
    def negotiate(message: dict[str, Any]) -> dict[str, Any]:
        trace("IN", "negotiate", message)
        inbox.receive_negotiate(message, own_sub_game)
        return negotiate_reply

    @mcp.tool
    def receive_turn(message: dict[str, Any]) -> dict[str, Any]:
        trace("IN", "receive_turn", message)
        inbox.receive_turn(message)
        return {"ok": True}

    @mcp.tool
    def submit_audit(payload: dict[str, Any]) -> dict[str, Any]:
        trace("IN", "submit_audit", payload)
        inbox.receive_audit(payload)
        return {"ok": True}

    @mcp.tool
    def receive_control(message: dict[str, Any]) -> dict[str, Any]:
        trace("IN", "receive_control", message)
        return {"ok": True}
