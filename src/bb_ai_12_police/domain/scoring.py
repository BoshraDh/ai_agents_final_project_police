"""Fixed scoring table (book Appendix ו, binding — do not change these numbers).

| outcome            | cop score | thief score |
|---------------------|-----------|-------------|
| captured             | 20        | 5           |
| survived             | 5         | 10          |
| tie (series-level)   | 2         | 2           |
| technical_loss       | 0         | 0           |
"""

from __future__ import annotations

from dataclasses import dataclass

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


@dataclass(frozen=True, slots=True)
class SeriesScore:
    """The aggregate result of one full match (all sub-games between two groups)."""

    sub_game_totals: dict[str, int]
    tie_award_applied: bool
    total_score: dict[str, int]
    winner_group: str | None
    series_tie: bool


def sub_game_scores(
    outcome: GameOutcome, our_role: Role, our_group: str, their_group: str
) -> dict[str, int]:
    """One sub-game's points keyed by group id, from this peer's point of view."""
    both = scores_for_both(outcome)
    their_role = Role.THIEF if our_role is Role.POLICE else Role.POLICE
    return {our_group: both[our_role], their_group: both[their_role]}


def score_series(per_sub_game: list[dict[str, int]]) -> SeriesScore:
    """Sum the sub-games, then apply the SERIES-level tie award.

    The tie rule is a decider for the whole match, not a sub-game outcome: the
    book's sub-game table has no tie row at all, while the Tie Rule states that
    if the cumulative score of all sub-games between a pair of groups ends level,
    each group receives `TIE_SCORE`. Filing the bare sum instead is exactly how
    a 45-45 was reported where 47-47 was correct.

    `per_sub_game` is one `{group_id: points}` mapping per sub-game, every entry
    naming the same two groups, so a side missing from one sub-game is rejected
    rather than silently scored zero.
    """
    if not per_sub_game:
        raise ValueError("a series needs at least one sub-game to score")
    groups = sorted(per_sub_game[0])
    if len(groups) != 2:
        raise ValueError(f"scoring is defined for exactly two groups, got {groups}")
    for entry in per_sub_game:
        if sorted(entry) != groups:
            raise ValueError(f"sub-game names {sorted(entry)}, expected {groups}")

    totals = {g: sum(entry[g] for entry in per_sub_game) for g in groups}
    level = totals[groups[0]] == totals[groups[1]]
    final = {g: totals[g] + (TIE_SCORE if level else 0) for g in groups}
    return SeriesScore(
        sub_game_totals=totals,
        tie_award_applied=level,
        total_score=final,
        winner_group=None if level else max(final, key=lambda g: final[g]),
        series_tie=level,
    )
