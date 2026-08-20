"""SHA-256 commit-reveal sealing (book's Commit->Acknowledge->Reveal->Audit,
ch.5.3 — confirmed against the book text: `Hcommit = SHA256(canonical_json(
{...payload, "nonce": nonce}))`, i.e. the nonce is one more field inside the
single canonically-serialized record, not appended outside it. The book's
own reference formula covers `{state, move, intent, nonce}` plus the hint,
step number, and role; this module stays generic over `payload`'s shape —
callers decide which fields to include. `CommitRevealLog` accumulates one
sealed entry per turn and can audit the whole sequence after the fact,
which is what "a mutual post-game audit re-verifies every step" (FR-9)
actually checks. The wire-level Commit/Acknowledge/Reveal message exchange
between peers is not implemented here — see `docs/PRD_security_crypto.md`
for why that stays a documented open item.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass, field
from typing import Any


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def generate_nonce() -> str:
    return secrets.token_hex(16)


def compute_commitment(payload: dict[str, Any], nonce: str) -> str:
    """Hcommit = SHA256(canonical_json({**payload, "nonce": nonce})) — book ch.5.3."""
    record = {**payload, "nonce": nonce}
    material = canonical_json(record)
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
