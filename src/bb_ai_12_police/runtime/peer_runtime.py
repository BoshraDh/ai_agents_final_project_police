"""Turn-loop for one standalone peer process — the real per-round protocol.

Starts this peer's MCP server in a background thread, then for each round:
decides a move, seals it (`CommitRevealLog`), exchanges commit+reveal with
the opponent (`mcp/client.py`), and updates `BeliefState`/`PheromoneField`
from what the opponent actually revealed. `GamePhaseMachine` enforces the
legal per-round phase sequence; a network failure moves the phase to
`TECHNICAL_LOSS`. After each round, `domain.rules.outcome_after_step`
checks for capture/survival on the just-updated (honestly-relayed, hence
exact) `BeliefState` and stops the loop early when either is reached —
both peers independently reach the same conclusion from the same round's
revealed positions, no extra coordination needed. See
`docs/PRD_turn_protocol.md` for the full design reasoning.
"""

from __future__ import annotations

import threading
import time

from bb_ai_12_police.crypto.commit_reveal import CommitRevealLog
from bb_ai_12_police.domain.barriers import BarrierSet
from bb_ai_12_police.domain.belief import BeliefState
from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.pheromones import PheromoneField
from bb_ai_12_police.domain.protocol import Direction, GameOutcome, Role
from bb_ai_12_police.domain.rules import cop_and_thief_positions, outcome_after_step
from bb_ai_12_police.domain.scoring import scores_for_both
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
        role: Role,
        survival_threshold: int,
        reveal_wait_timeout_sec: float,
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
        self.role = role
        self.survival_threshold = survival_threshold
        self.reveal_wait_timeout_sec = reveal_wait_timeout_sec
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
        self.outcome = GameOutcome.ONGOING
        self.final_turn: int | None = None

    def start_server(self, startup_delay_sec: float = 1.0) -> None:
        """Bind this peer's inbound MCP server in a background thread."""
        mcp = build_server(self.server_name, self.turn_handler, self.reveal_wait_timeout_sec)
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

    def _check_outcome(self, turn: int) -> GameOutcome:
        cop_pos, thief_pos = cop_and_thief_positions(
            self.role, self.belief.own_position, self.belief.opponent_position
        )
        return outcome_after_step(cop_pos, thief_pos, turn, self.survival_threshold)

    def run_turn_loop(self, turns: int) -> None:
        """Play up to `turns` real rounds; stops early on capture or survival."""
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

            self.outcome = self._check_outcome(turn)
            if self.outcome is not GameOutcome.ONGOING:
                self.final_turn = turn
                scores = {r.value: s for r, s in scores_for_both(self.outcome).items()}
                print(f"[turn {turn}] GAME OVER: {self.outcome.value} — scores {scores}")
                break
