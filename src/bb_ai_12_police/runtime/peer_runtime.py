"""Turn-loop skeleton for one standalone peer process.

Starts this peer's MCP server in a background thread, then repeatedly calls
the opponent's `receive_move` tool. Stage 2 only proves the wire round-trips
end-to-end — no strategy, crypto, or scoring yet, so every move sent is a
hardcoded STAY; `_decide_move` is replaced by the real brain in stage 3.
"""

from __future__ import annotations

import threading
import time

from bb_ai_12_police.domain.protocol import Direction
from bb_ai_12_police.mcp.client import McpTransport
from bb_ai_12_police.mcp.server import run_server


class PeerRuntime:
    """One standalone agent process: server thread + outbound turn loop."""

    def __init__(self, host: str, port: int, opponent_url: str) -> None:
        self.host = host
        self.port = port
        self.transport = McpTransport(opponent_url)

    def start_server(self, startup_delay_sec: float = 1.0) -> None:
        """Bind this peer's inbound MCP server in a background thread."""
        thread = threading.Thread(
            target=run_server, args=(self.host, self.port), daemon=True
        )
        thread.start()
        time.sleep(startup_delay_sec)  # let uvicorn bind before we call out

    def _decide_move(self, turn: int) -> Direction:
        """Stage 2 stub — always STAY. Stage 3 replaces this with a brain."""
        return Direction.STAY

    def run_turn_loop(self, turns: int) -> None:
        """Send `turns` hardcoded moves to the opponent, printing each reply."""
        for turn in range(1, turns + 1):
            move = self._decide_move(turn)
            reply = self.transport.send_move(move.value, turn)
            print(f"[turn {turn}] sent {move.value!r}, opponent replied {reply!r}")
