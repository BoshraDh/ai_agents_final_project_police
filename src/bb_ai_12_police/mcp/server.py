"""FastMCP server exposing this peer's inbound move endpoint.

Stage 2: proves the P2P wire works end-to-end. `receive_move` is the only
inbound entry point an opponent peer calls each turn; the hardcoded STAY
reply is replaced by the real strategy brain in stage 3.
"""

from __future__ import annotations

from fastmcp import FastMCP

from bb_ai_12_police.domain.protocol import Direction

mcp = FastMCP(name="bb-ai-12-police")


@mcp.tool
def receive_move(direction: str, turn: int) -> dict[str, str | int]:
    """Receive the opponent's move for this turn and reply with our own.

    Stage 2 stub: always replies STAY regardless of what was received.
    """
    print(f"[bb-ai-12-police] opponent played {direction!r} on turn {turn}")
    return {"direction": Direction.STAY.value, "turn": turn}


def run_server(host: str, port: int) -> None:
    """Block, serving MCP over streamable HTTP at http://host:port/mcp."""
    mcp.run(transport="http", host=host, port=port, path="/mcp")
