"""Step-0 declaration: a sealed statement of this peer's hardware/software
environment, exchanged once before a match begins (book's Step-0).

"Signed" here means sealed via the same SHA-256 commit-reveal primitive
used for moves (`crypto/commit_reveal.py`) — no asymmetric-key signing
scheme has been confirmed from the book text in this session, so this
module does not invent one. If the book specifies real public-key
signatures for Step-0, this needs revisiting before a real submission
(see `docs/TODO.md`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bb_ai_12_police.crypto.commit_reveal import compute_commitment, generate_nonce
from bb_ai_12_police.shared.sysinfo import collect_sysinfo


@dataclass(frozen=True, slots=True)
class Step0Declaration:
    payload: dict[str, Any]
    nonce: str
    commitment: str

    @classmethod
    def create(cls, team_code: str) -> Step0Declaration:
        payload = {"team_code": team_code, **collect_sysinfo()}
        nonce = generate_nonce()
        commitment = compute_commitment(payload, nonce)
        return cls(payload=payload, nonce=nonce, commitment=commitment)

    def verify(self) -> bool:
        return compute_commitment(self.payload, self.nonce) == self.commitment
