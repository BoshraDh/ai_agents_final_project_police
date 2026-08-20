"""Turn-loop for one standalone peer process.

Starts this peer's MCP server in a background thread (still the stage-2
STAY-echo stub — see `mcp/server.py`), then repeatedly asks the resolved
brain for this turn's real move, sends it (with a real trash-talk hint) to
the opponent, and updates the local `BeliefState` and `PheromoneField`.
Full bidirectional synchronized turn-taking (so the inbound stub also
replies with a real move/hint) is deferred to the negotiation/turn-handler
work in a later stage — see `docs/PRD_strategy.md` for why that boundary
was drawn here.
"""

from __future__ import annotations

import threading
import time

from bb_ai_12_police.domain.barriers import BarrierSet
from bb_ai_12_police.domain.belief import BeliefState
from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.pheromones import PheromoneField
from bb_ai_12_police.domain.protocol import Direction
from bb_ai_12_police.llm.provider_base import TrashTalkProvider
from bb_ai_12_police.mcp.client import McpTransport
from bb_ai_12_police.mcp.server import run_server
from bb_ai_12_police.strategy.base import BrainBase


class PeerRuntime:
    """One standalone agent process: server thread + outbound turn loop."""

    def __init__(
        self,
        host: str,
        port: int,
        opponent_url: str,
        board: Board,
        barriers: BarrierSet,
        belief: BeliefState,
        brain: BrainBase,
        trash_talk: TrashTalkProvider,
        opponent_scent: PheromoneField,
    ) -> None:
        self.host = host
        self.port = port
        self.transport = McpTransport(opponent_url)
        self.board = board
        self.barriers = barriers
        self.belief = belief
        self.brain = brain
        self.trash_talk = trash_talk
        self.opponent_scent = opponent_scent

    def start_server(self, startup_delay_sec: float = 1.0) -> None:
        """Bind this peer's inbound MCP server in a background thread."""
        thread = threading.Thread(
            target=run_server, args=(self.host, self.port), daemon=True
        )
        thread.start()
        time.sleep(startup_delay_sec)  # let uvicorn bind before we call out

    def _decide_move(self) -> Direction:
        return self.brain.decide_move(
            self.board, self.barriers, self.belief.own_position, self.belief.opponent_position
        )

    def run_turn_loop(self, turns: int) -> None:
        """Send `turns` real-strategy moves + hints, printing each reply."""
        for turn in range(1, turns + 1):
            move = self._decide_move()
            self.belief.apply_own_move(move)
            hint = self.trash_talk.hint(turn)
            reply = self.transport.send_move(move.value, turn, hint)
            self.belief.apply_opponent_move(Direction(reply["direction"]))
            self.opponent_scent.step(self.belief.opponent_position)
            print(f"[turn {turn}] sent {move.value!r} ({hint!r}), opponent replied {reply!r}")
