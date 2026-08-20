"""Fixed scoring table (book Appendix ו, binding — do not change these numbers).

| outcome            | cop score | thief score |
|---------------------|-----------|-------------|
| captured             | 20        | 5           |
| survived             | 5         | 10          |
| tie (series-level)   | 2         | 2           |
| technical_loss       | 0         | 0           |
"""

from __future__ import annotations

from bb_ai_12_police.domain.protocol import GameOutcome, Role

CAPTURE_COP = 20
CAPTURE_THIEF = 5
SURVIVAL_COP = 5
SURVIVAL_THIEF = 10
TIE_SCORE = 2
TECHNICAL_LOSS = 0

_SCORE_TABLE: dict[GameOutcome, dict[Role, int]] = {
    GameOutcome.CAPTURED: {Role.POLICE: CAPTURE_COP, Role.THIEF: CAPTURE_THIEF},
    GameOutcome.SURVIVED: {Role.POLICE: SURVIVAL_COP, Role.THIEF: SURVIVAL_THIEF},
    GameOutcome.TIE: {Role.POLICE: TIE_SCORE, Role.THIEF: TIE_SCORE},
    GameOutcome.TECHNICAL_LOSS: {Role.POLICE: TECHNICAL_LOSS, Role.THIEF: TECHNICAL_LOSS},
}


def score_for(outcome: GameOutcome, role: Role) -> int:
    """The fixed point award for `role` when a sub-game ends in `outcome`.

    Raises `KeyError` for `GameOutcome.ONGOING`, which is never scoreable.
    """
    return _SCORE_TABLE[outcome][role]


def scores_for_both(outcome: GameOutcome) -> dict[Role, int]:
    """Convenience: both roles' scores for one terminal outcome, at once."""
    return dict(_SCORE_TABLE[outcome])
