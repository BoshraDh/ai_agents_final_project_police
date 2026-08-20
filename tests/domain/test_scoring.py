from bb_ai_12_police.domain.protocol import GameOutcome, Role
from bb_ai_12_police.domain.scoring import score_for, scores_for_both


def test_capture_scores_match_book_table():
    assert score_for(GameOutcome.CAPTURED, Role.POLICE) == 20
    assert score_for(GameOutcome.CAPTURED, Role.THIEF) == 5


def test_survival_scores_match_book_table():
    assert score_for(GameOutcome.SURVIVED, Role.POLICE) == 5
    assert score_for(GameOutcome.SURVIVED, Role.THIEF) == 10


def test_tie_and_technical_loss_are_symmetric():
    assert scores_for_both(GameOutcome.TIE) == {Role.POLICE: 2, Role.THIEF: 2}
    assert scores_for_both(GameOutcome.TECHNICAL_LOSS) == {Role.POLICE: 0, Role.THIEF: 0}
