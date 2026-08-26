import pytest

from bb_ai_12_police.domain.protocol import GameOutcome, Role
from bb_ai_12_police.domain.scoring import (
    score_for,
    score_series,
    scores_for_both,
    sub_game_scores,
)


def test_capture_scores_match_book_table():
    assert score_for(GameOutcome.CAPTURED, Role.POLICE) == 20
    assert score_for(GameOutcome.CAPTURED, Role.THIEF) == 5


def test_survival_scores_match_book_table():
    assert score_for(GameOutcome.SURVIVED, Role.POLICE) == 5
    assert score_for(GameOutcome.SURVIVED, Role.THIEF) == 10


def test_tie_and_technical_loss_are_symmetric():
    assert scores_for_both(GameOutcome.TIE) == {Role.POLICE: 2, Role.THIEF: 2}
    assert scores_for_both(GameOutcome.TECHNICAL_LOSS) == {Role.POLICE: 0, Role.THIEF: 0}


def test_sub_game_scores_are_keyed_by_group_from_our_point_of_view():
    assert sub_game_scores(GameOutcome.SURVIVED, Role.THIEF, "bb-ai-12", "SMNGRP05") == {
        "bb-ai-12": 10, "SMNGRP05": 5
    }
    assert sub_game_scores(GameOutcome.CAPTURED, Role.POLICE, "bb-ai-12", "SMNGRP05") == {
        "bb-ai-12": 20, "SMNGRP05": 5
    }


def test_the_2026_08_26_series_totals_47_47_not_45_45():
    # The real friendly series vs SMNGRP05: thief on 1/3/5, police on 2/4/6,
    # every sub-game ending in survival. The bare sum is 45-45; the series tie
    # award then applies once, to both sides. We filed 45-45 and were corrected.
    per_sub_game = [
        sub_game_scores(
            GameOutcome.SURVIVED,
            Role.THIEF if n % 2 == 1 else Role.POLICE,
            "bb-ai-12",
            "SMNGRP05",
        )
        for n in range(1, 7)
    ]

    result = score_series(per_sub_game)

    assert result.sub_game_totals == {"bb-ai-12": 45, "SMNGRP05": 45}
    assert result.tie_award_applied is True
    assert result.total_score == {"bb-ai-12": 47, "SMNGRP05": 47}
    assert result.series_tie is True
    assert result.winner_group is None


def test_no_tie_award_when_the_series_is_not_level():
    per_sub_game = [
        sub_game_scores(GameOutcome.CAPTURED, Role.POLICE, "bb-ai-12", "SMNGRP05"),
        sub_game_scores(GameOutcome.SURVIVED, Role.THIEF, "bb-ai-12", "SMNGRP05"),
    ]

    result = score_series(per_sub_game)

    assert result.total_score == {"bb-ai-12": 30, "SMNGRP05": 10}
    assert result.tie_award_applied is False
    assert result.winner_group == "bb-ai-12"


def test_a_sub_game_missing_a_group_is_rejected_not_scored_zero():
    with pytest.raises(ValueError, match="expected"):
        score_series([{"bb-ai-12": 10, "SMNGRP05": 5}, {"bb-ai-12": 10, "typo": 5}])


def test_an_empty_series_is_rejected():
    with pytest.raises(ValueError, match="at least one sub-game"):
        score_series([])
