"""Turn-loop for one standalone peer process — the real per-round protocol.

Starts this peer's MCP server (now exposing submit_commit/submit_reveal —
see `mcp/server.py`) in a background thread, then for each round: decides a
move via the resolved brain, builds a state snapshot + intent, seals it
(`CommitRevealLog`, for the eventual end-of-game audit), registers the
reveal locally (`TurnHandler.prepare_own_reveal`) so an inbound call from
the opponent can already answer with it, sends the commit then the reveal
to the opponent (receiving the opponent's own reveal back in the same
round trip — see `mcp/client.py`), and updates `BeliefState`/
`PheromoneField` from what the opponent actually revealed.
`GamePhaseMachine` enforces the legal per-round phase sequence; a failure
during the commit-send or reveal-send moves the phase to `TECHNICAL_LOSS`
and re-raises (this session's interpretation of the book's diagram, which
doesn't enumerate every possible network-failure point — see
`docs/PRD_security_crypto.md`).
"""

from __future__ import annotations

import threading
import time

from bb_ai_12_police.crypto.commit_reveal import CommitRevealLog
from bb_ai_12_police.domain.barriers import BarrierSet
from bb_ai_12_police.domain.belief import BeliefState
from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.pheromones import PheromoneField
from bb_ai_12_police.domain.protocol import Direction
from bb_ai_12_police.llm.provider_base import TrashTalkProvider
from bb_ai_12_police.mcp.client import McpTransport
from bb_ai_12_police.mcp.server import build_server, run_server
from bb_ai_12_police.peer.turn_handler import TurnHandler
from bb_ai_12_police.runtime.state_machine import GamePhaseMachine
from bb_ai_12_police.strategy.base import BrainBase


class PeerRuntime:
    """One standalone agent process: server thread + outbound round loop."""

    def __init__(
        self,
        host: str,
        port: int,
        opponent_url: str,
        server_name: str,
        board: Board,
        barriers: BarrierSet,
        belief: BeliefState,
        brain: BrainBase,
        trash_talk: TrashTalkProvider,
        opponent_scent: PheromoneField,
        commit_log: CommitRevealLog,
        turn_handler: TurnHandler,
    ) -> None:
        self.host = host
        self.port = port
        self.server_name = server_name
        self.transport = McpTransport(opponent_url)
        self.board = board
        self.barriers = barriers
        self.belief = belief
        self.brain = brain
        self.trash_talk = trash_talk
        self.opponent_scent = opponent_scent
        self.commit_log = commit_log
        self.turn_handler = turn_handler
        self.machine = GamePhaseMachine()

    def start_server(self, startup_delay_sec: float = 1.0) -> None:
        """Bind this peer's inbound MCP server in a background thread."""
        mcp = build_server(self.server_name, self.turn_handler)
        thread = threading.Thread(
            target=run_server, args=(mcp, self.host, self.port), daemon=True
        )
        thread.start()
        time.sleep(startup_delay_sec)  # let uvicorn bind before we call out

    def _decide_move(self) -> Direction:
        return self.brain.decide_move(
            self.board, self.barriers, self.belief.own_position, self.belief.opponent_position
        )

    def _state_snapshot(self, turn: int) -> dict[str, object]:
        return {
            "own_position": list(self.belief.own_position.as_tuple()),
            "opponent_position": list(self.belief.opponent_position.as_tuple()),
            "turn": turn,
        }

    def run_turn_loop(self, turns: int) -> None:
        """Play `turns` real rounds via the book's commit-reveal protocol."""
        for turn in range(1, turns + 1):
            self.machine.transition("COMPUTING_MOVE")
            move = self._decide_move()
            hint = self.trash_talk.hint(turn)
            intent = "truth"
            payload = {"state": self._state_snapshot(turn), "move": move.value, "intent": intent}

            try:
                sealed = self.commit_log.seal(turn, payload)
                self.turn_handler.prepare_own_reveal(turn, move.value, hint, intent)
                self.transport.send_commit(sealed.commitment, turn)
            except Exception:
                self.machine.transition("TECHNICAL_LOSS")
                raise
            self.machine.transition("COMMITTING")

            self.machine.transition("AWAITING_REVEAL")
            try:
                reply = self.transport.send_reveal(move.value, hint, intent, turn)
                opponent_move = Direction(reply["move"])
            except Exception:
                self.machine.transition("TECHNICAL_LOSS")
                raise

            self.belief.apply_own_move(move)
            self.belief.apply_opponent_move(opponent_move)
            self.opponent_scent.step(self.belief.opponent_position)
            self.machine.transition("VERIFYING")
            self.machine.transition("WAITING_FOR_OPPONENT")

            print(
                f"[turn {turn}] committed {sealed.commitment[:8]}..., revealed "
                f"{move.value!r} ({hint!r}), opponent revealed {reply!r}"
            )
