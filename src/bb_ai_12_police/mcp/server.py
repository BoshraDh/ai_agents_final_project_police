"""FastMCP server exposing this peer's inbound move endpoint.

Stage 2: proves the P2P wire works end-to-end. `receive_move` is the only
inbound entry point an opponent peer calls each turn; the hardcoded STAY
reply is replaced by the real strategy brain in stage 3. Stage 4 adds the
`hint` field (free-text banter, capped at `hint_max_words` by the sender's
`TrashTalkProvider`) — the inbound stub still replies with a fixed line,
consistent with the stage-3 decision to leave real inbound replies to a
later synchronized turn-taking protocol (see `docs/PRD_strategy.md`).
"""

from __future__ import annotations

from fastmcp import FastMCP

from bb_ai_12_police.domain.protocol import Direction

mcp = FastMCP(name="bb-ai-12-police")

_STUB_HINT = "..."


@mcp.tool
def receive_move(direction: str, turn: int, hint: str = "") -> dict[str, str | int]:
    """Receive the opponent's move and hint for this turn; reply with our own.

    Stage 2/4 stub: always replies STAY with a fixed placeholder hint.
    """
    print(f"[bb-ai-12-police] opponent played {direction!r} on turn {turn} ({hint!r})")
    return {"direction": Direction.STAY.value, "turn": turn, "hint": _STUB_HINT}


def run_server(host: str, port: int) -> None:
    """Block, serving MCP over streamable HTTP at http://host:port/mcp."""
    mcp.run(transport="http", host=host, port=port, path="/mcp")
