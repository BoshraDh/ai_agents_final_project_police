"""Smoke tests for the live GUI: construct, render one turn, close.

`show=False` withdraws the window immediately — these tests verify the
widget tree builds and updates without exceptions, not visual appearance
(that needs a human watching a real run).
"""

from __future__ import annotations

from bb_ai_12_police.domain.belief import BeliefState
from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.protocol import Position
from bb_ai_12_police.gui.live_gui import LiveGui


def test_live_gui_constructs_renders_and_closes_without_error():
    gui = LiveGui(Board(size=7), show=False)
    try:
        belief = BeliefState(own_position=Position(0, 0), opponent_position=Position(3, 3))
        gui.render_turn(1, belief, "You can't hide forever.")
    finally:
        gui.close()
