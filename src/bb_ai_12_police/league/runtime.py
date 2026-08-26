"""Game loop for the league kit's 4-tool protocol (negotiate/receive_turn/
submit_audit) for opponents that speak the kit's shape instead of ours.
Real positions are never disclosed mid-game -- only `smell_grid` -- so
each side's brain is fed a best-guess position from `league/smell.py`.
"""

from __future__ import annotations

import asyncio

from bb_ai_12_police.crypto.commit_reveal import CommitRevealLog
from bb_ai_12_police.crypto.step0 import Step0Declaration
from bb_ai_12_police.domain.barriers import BarrierSet
from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.pheromones import PheromoneField
from bb_ai_12_police.domain.protocol import GameOutcome, Position, Role
from bb_ai_12_police.league.client import LeagueTransport
from bb_ai_12_police.league.inbox import LeagueInbox
from bb_ai_12_police.league.messages import build_audit, build_negotiate, build_turn
from bb_ai_12_police.league.outcome import absorb_inbound, build_claim_response
from bb_ai_12_police.league.smell import guess_position_from_smell
from bb_ai_12_police.league.terms import terms_signature, to_wire_terms, verify_signature
from bb_ai_12_police.llm.provider_base import TrashTalkProvider
from bb_ai_12_police.strategy.base import BrainBase

# A single-shot negotiate attempt was found live (2026-08-24, independently
# confirmed via a role-swapped control test, not the opponent's diagnosis)
# to fail whenever a sub-game is launched immediately after the previous one
# -- correlated with launch timing, not role or transport. No retry existed
# to recover from a single missed window; add one instead of relying on a
# manual re-run.
_NEGOTIATE_ATTEMPTS = 2
_NEGOTIATE_RETRY_DELAY_SEC = 10.0


class LeagueRuntime:
    """One sub-game played over the league kit's wire protocol."""

    def __init__(
        self,
        role: Role,
        own_position: Position,
        opponent_start: Position,
        board: Board,
        barriers: BarrierSet,
        brain: BrainBase,
        trash_talk: TrashTalkProvider,
        own_scent: PheromoneField,
        survival_threshold: int,
        shared_config: dict,
        group_id: str,
        members: list[str],
        transport: LeagueTransport,
        inbox: LeagueInbox,
        step0: Step0Declaration,
        # Raised 30->60->180: an opponent that deliberately pauses between
        # sub-games (found live 2026-08-25, aviayeli's sub-game-pause fix)
        # needs us to still be waiting when they actually dial, not give up
        # first and read their late negotiate as a fresh failure.
        handshake_timeout_sec: float = 180.0,
        turn_timeout_sec: float = 60.0,
    ) -> None:
        self.role = role
        self.own_position = own_position
        self.opponent_guess = opponent_start
        self.board = board
        self.barriers = barriers
        self.brain = brain
        self.trash_talk = trash_talk
        self.own_scent = own_scent
        self.survival_threshold = survival_threshold
        self.shared_config = shared_config
        self.group_id = group_id
        self.members = members
        self.transport = transport
        self.inbox = inbox
        self.step0 = step0
        self.handshake_timeout_sec = handshake_timeout_sec
        self.turn_timeout_sec = turn_timeout_sec
        self.commit_log = CommitRevealLog()
        self.outcome = GameOutcome.ONGOING
        self.final_turn: int | None = None
        self._pending_claim: list[int] | None = None

    async def negotiate(self, sub_game_number: int = 1) -> bool:
        terms = to_wire_terms(self.shared_config)
        nonce = self.step0.nonce
        signature = terms_signature(terms, nonce)
        message = build_negotiate(
            terms, nonce, signature, self.group_id, self.members, self.role.value, sub_game_number
        )
        for attempt in range(1, _NEGOTIATE_ATTEMPTS + 1):
            await self.transport.negotiate(message)
            try:
                theirs = self.inbox.wait_for_negotiate(self.handshake_timeout_sec)
            except TimeoutError:
                if attempt == _NEGOTIATE_ATTEMPTS:
                    raise
                await asyncio.sleep(_NEGOTIATE_RETRY_DELAY_SEC)
                continue
            return theirs["terms"] == terms and verify_signature(
                theirs["terms"], theirs["nonce"], theirs["signature"]
            )
        raise RuntimeError("unreachable")  # pragma: no cover

    async def play(self, turns: int) -> GameOutcome:
        for turn in range(1, turns + 1):
            self._play_one_turn(turn)
            try:
                inbound = await self._exchange_turn(turn)
            except TimeoutError:
                # Opponent went silent right at our own self-declared win
                # boundary -- that doesn't undo what we already know locally.
                if self._survived_now:
                    self.outcome = GameOutcome.SURVIVED
                    self.final_turn = turn
                break
            self._absorb_inbound(inbound)
            if self.outcome is not GameOutcome.ONGOING:
                self.final_turn = turn
                break
        try:
            reply = await self._send_audit()
            print(f"[league] submit_audit reply: {reply!r}")
        except Exception as exc:  # noqa: BLE001 - non-fatal; outcome is already decided
            print(f"[league] submit_audit failed: {exc!r}")
        return self.outcome

    def _play_one_turn(self, turn: int) -> None:
        direction = self.brain.decide_move(
            self.board, self.barriers, self.own_position, self.opponent_guess
        )
        self.own_position = self.own_position.moved(direction)
        self.own_scent.step(self.own_position)
        payload = {"state": self.own_position.as_tuple(), "move": direction.value, "turn": turn}
        self._sealed = self.commit_log.seal(turn, payload)
        self._hint = self.trash_talk.hint(turn)
        self._survived_now = self.role is Role.THIEF and turn >= self.survival_threshold

    async def _exchange_turn(self, turn: int) -> dict:
        capture_claim = self.own_position if self.role is Role.POLICE else None
        claim_response = None
        if self.role is Role.THIEF and self._pending_claim is not None:
            claim_response = build_claim_response(self._pending_claim, self.own_position)
        win_claim = {"type": "survival"} if self._survived_now else None
        message = build_turn(
            turn,
            self.role,
            self._hint,
            self.own_scent,
            self._sealed.commitment,
            capture_claim,
            claim_response,
            win_claim,
        )
        reply = await self.transport.send_turn(message)
        print(f"[league] receive_turn reply (turn {turn}): {reply!r}")
        return self.inbox.wait_for_turn(turn, self.turn_timeout_sec)

    def _absorb_inbound(self, inbound: dict) -> None:
        self.opponent_guess = guess_position_from_smell(
            inbound.get("smell_grid", {}), self.opponent_guess
        )
        self.outcome, self._pending_claim = absorb_inbound(
            self.role, self._survived_now, inbound
        )

    async def _send_audit(self) -> dict:
        result_claim = {
            "type": {
                GameOutcome.CAPTURED: "capture",
                GameOutcome.SURVIVED: "survival",
            }.get(self.outcome, "timeout")
        }
        envelope = build_audit(self.role, self.commit_log, result_claim, self.step0)
        return await self.transport.send_audit(envelope)
