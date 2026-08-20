"""FastMCP server exposing this peer's inbound turn-protocol endpoints.

Two tools, matching the book's confirmed Commit->Acknowledge->Reveal
sequence (ch.5.3) applied once per round (ch.4 confirms a "turn" means both
agents have moved). `submit_commit` records the opponent's commitment hash
and acks it. `submit_reveal` records the opponent's revealed move/hint/
intent and replies with this peer's own already-prepared reveal for the
same round — so whichever side calls first completes the exchange for
both. `submit_reveal` raises if no commit preceded it (see
`peer/turn_handler.py`), turning a protocol violation into an immediate,
visible failure instead of a silent trust gap.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from bb_ai_12_police.peer.turn_handler import TurnHandler


def build_server(name: str, turn_handler: TurnHandler) -> FastMCP:
    mcp = FastMCP(name=name)

    @mcp.tool
    def submit_commit(h_commit: str, turn: int) -> dict[str, Any]:
        turn_handler.receive_commit(turn, h_commit)
        return {"received": True, "turn": turn}

    @mcp.tool
    def submit_reveal(move: str, hint: str, intent: str, turn: int) -> dict[str, Any]:
        turn_handler.receive_reveal(turn, move, hint, intent)
        own = turn_handler.own_reveal(turn)
        return {"move": own.move, "hint": own.hint, "intent": own.intent, "turn": turn}

    return mcp


def run_server(mcp: FastMCP, host: str, port: int) -> None:
    """Block, serving MCP over streamable HTTP at http://host:port/mcp."""
    mcp.run(transport="http", host=host, port=port, path="/mcp")
