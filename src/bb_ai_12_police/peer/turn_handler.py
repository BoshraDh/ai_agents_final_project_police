"""Real per-round turn-taking protocol, built on the book's confirmed
Commit(hash-only) -> Acknowledge(locked) -> Reveal(move+hint+intent, nonce
still hidden) sequence (book ch.5.3), applied once per round to a shared
`turn` number.

Confirmed from the book this session: a "turn" is a full ROUND in which
both agents move — ch.4's pheromone-decay timing runs only "after both the
cop and the thief have completed their move" for that round, not strict
chess-style alternation. Each peer proactively drives its own round loop
and calls the opponent for both phases; whichever call arrives first at a
peer's server gets that peer's own already-committed reveal back in the
same round trip, so the exchange is idempotent no matter who calls first.
Final nonce disclosure (for the end-of-game mutual audit) is handled by
`crypto.commit_reveal.CommitRevealLog`, not here.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Reveal:
    turn: int
    move: str
    hint: str
    intent: str


@dataclass(slots=True)
class TurnHandler:
    """Tracks this peer's own committed reveal and the opponent's, per round."""

    _own_reveals: dict[int, Reveal] = field(default_factory=dict)
    _received_commits: dict[int, str] = field(default_factory=dict)
    _received_reveals: dict[int, Reveal] = field(default_factory=dict)

    def prepare_own_reveal(self, turn: int, move: str, hint: str, intent: str) -> None:
        """Called locally once this peer has decided+sealed its round-`turn` move."""
        self._own_reveals[turn] = Reveal(turn=turn, move=move, hint=hint, intent=intent)

    def own_reveal(self, turn: int) -> Reveal:
        if turn not in self._own_reveals:
            raise ValueError(f"no own reveal prepared for round {turn} yet")
        return self._own_reveals[turn]

    def wait_for_own_reveal(
        self, turn: int, timeout_sec: float, poll_interval_sec: float = 0.02
    ) -> Reveal:
        """Blocks until this peer has locally prepared its round-`turn` reveal.

        The book's Acknowledge step exists to "ensure reveal only after both
        sides have committed" (ch.5.3); two independently-started processes
        have no other shared clock to enforce that with, so instead of
        answering an inbound reveal request immediately (and possibly before
        this peer has even decided its own move for the round), the
        responder waits for its own local preparation to catch up — turning
        the round into an implicit rendezvous rather than a race.
        """
        deadline = time.monotonic() + timeout_sec
        while turn not in self._own_reveals:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"timed out waiting to prepare own reveal for round {turn}")
            time.sleep(poll_interval_sec)
        return self._own_reveals[turn]

    def receive_commit(self, turn: int, h_commit: str) -> None:
        self._received_commits[turn] = h_commit

    def has_received_commit(self, turn: int) -> bool:
        return turn in self._received_commits

    def receive_reveal(self, turn: int, move: str, hint: str, intent: str) -> Reveal:
        """Records the opponent's reveal for `turn`.

        Raises if no commit was received first for this round — the book's
        Ack step exists precisely so a reveal never arrives before both
        sides have locked in their moves.
        """
        if turn not in self._received_commits:
            raise ValueError(f"protocol violation: reveal for round {turn} with no prior commit")
        reveal = Reveal(turn=turn, move=move, hint=hint, intent=intent)
        self._received_reveals[turn] = reveal
        return reveal

    def opponent_reveal(self, turn: int) -> Reveal | None:
        return self._received_reveals.get(turn)
