"""Pure outcome-detection from one inbound league-protocol turn message —
split out of `runtime.py` to stay under the 150-line cap.
"""

from __future__ import annotations

from typing import Any

from bb_ai_12_police.domain.protocol import GameOutcome, Position, Role


def absorb_inbound(
    role: Role, survived_now: bool, inbound: dict[str, Any]
) -> tuple[GameOutcome, list[int] | None]:
    """Returns `(outcome, next_pending_claim)` for the thief's next turn."""
    if role is Role.POLICE:
        response = inbound.get("claim_response")
        if response is not None and response.get("caught"):
            return GameOutcome.CAPTURED, None
        if inbound.get("win_claim", {}).get("type") == "survival":
            return GameOutcome.SURVIVED, None
        return GameOutcome.ONGOING, None

    claim = inbound.get("capture_claim")
    next_claim = list(claim) if claim is not None else None
    if survived_now:
        return GameOutcome.SURVIVED, next_claim
    return GameOutcome.ONGOING, next_claim


def build_claim_response(pending_claim: list[int], own_position: Position) -> dict[str, Any]:
    r, c = pending_claim
    return {"claim": [r, c], "caught": own_position == Position(row=r, col=c)}
