"""SHA-256 commit-reveal sealing.

Deliberately follows the league's shared `copthief-league-protocol` kit
formula (https://github.com/Imreec/copthief-league-protocol), NOT the
book's own ch.5.3 literal code sample — a conscious, informed deviation
(2026-08-24) made because the actual opponent pool in this league has
converged on the kit's formula rather than the book's, and matching them
is what makes real matches possible. The book puts the nonce *inside* the
canonical JSON record; the kit instead does
`Hcommit = SHA256(canonical_json(payload) + "|" + nonce)` — nonce
pipe-concatenated *outside* the JSON, with `ensure_ascii=False`. See
`docs/TODO.md` for the full reasoning and the explicit trade-off this
was weighed against. `CommitRevealLog` accumulates one sealed entry per
turn and can audit the whole sequence after the fact, which is what "a
mutual post-game audit re-verifies every step" (FR-9) actually checks.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass, field
from typing import Any


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def generate_nonce() -> str:
    return secrets.token_hex(16)


def compute_commitment(payload: dict[str, Any], nonce: str) -> str:
    """Hcommit = SHA256(canonical_json(payload) + "|" + nonce) — league kit formula."""
    material = f"{canonical_json(payload)}|{nonce}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def verify_reveal(payload: dict[str, Any], nonce: str, commitment: str) -> bool:
    return compute_commitment(payload, nonce) == commitment


@dataclass(frozen=True, slots=True)
class SealedMove:
    turn: int
    payload: dict[str, Any]
    nonce: str
    commitment: str


@dataclass(slots=True)
class CommitRevealLog:
    """Accumulates sealed moves across a sub-game for a later audit pass."""

    _entries: list[SealedMove] = field(default_factory=list)

    def seal(self, turn: int, payload: dict[str, Any]) -> SealedMove:
        nonce = generate_nonce()
        commitment = compute_commitment(payload, nonce)
        entry = SealedMove(turn=turn, payload=payload, nonce=nonce, commitment=commitment)
        self._entries.append(entry)
        return entry

    def audit(self) -> bool:
        """True iff every sealed entry's reveal still matches its commitment."""
        return all(verify_reveal(e.payload, e.nonce, e.commitment) for e in self._entries)

    def tampered_turns(self) -> list[int]:
        return [
            e.turn for e in self._entries if not verify_reveal(e.payload, e.nonce, e.commitment)
        ]

    def entries(self) -> list[SealedMove]:
        """Read-only snapshot of the sealed moves, for building report artifacts."""
        return list(self._entries)
