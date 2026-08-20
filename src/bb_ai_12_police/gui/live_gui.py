"""Live GUI: local-truth-only view (book's no-omniscient-board rule).

Draws only what this peer actually knows: its own position and its tracked
`BeliefState` of the opponent, plus a turn/hint banner. Not the true global
board — `BeliefState` is exact only because moves are honestly relayed
pre-crypto/pre-deception (see `docs/PRD_strategy.md`); once that changes,
this view is still only ever drawing this peer's own belief, never a
peeked-at ground truth.
"""

from __future__ import annotations

import tkinter as tk

from bb_ai_12_police.domain.belief import BeliefState
from bb_ai_12_police.domain.board import Board

_CELL_SIZE = 40


class LiveGui:
    """One Tk window: grid canvas + turn banner. Call `render_turn` each turn."""

    def __init__(self, board: Board, show: bool = True) -> None:
        self.board = board
        self.root = tk.Tk()
        self.root.title("bb-ai-12 — live view (local truth only)")
        if not show:
            self.root.withdraw()
        size_px = board.size * _CELL_SIZE
        self.canvas = tk.Canvas(self.root, width=size_px, height=size_px, bg="white")
        self.canvas.pack()
        self.banner = tk.Label(self.root, text="Waiting for turn 1...", anchor="w")
        self.banner.pack(fill="x")
        self._draw_grid()

    def _draw_grid(self) -> None:
        extent = self.board.size * _CELL_SIZE
        for i in range(self.board.size + 1):
            self.canvas.create_line(0, i * _CELL_SIZE, extent, i * _CELL_SIZE)
            self.canvas.create_line(i * _CELL_SIZE, 0, i * _CELL_SIZE, extent)

    def render_turn(self, turn: int, belief: BeliefState, hint: str) -> None:
        self.canvas.delete("agent")
        self._draw_cell(belief.own_position.row, belief.own_position.col, "blue", "me")
        self._draw_cell(belief.opponent_position.row, belief.opponent_position.col, "red", "opp")
        self.banner.config(text=f"Turn {turn}: {hint!r}")
        self.root.update()

    def _draw_cell(self, row: int, col: int, color: str, tag: str) -> None:
        x0, y0 = col * _CELL_SIZE + 4, row * _CELL_SIZE + 4
        x1, y1 = x0 + _CELL_SIZE - 8, y0 + _CELL_SIZE - 8
        self.canvas.create_oval(x0, y0, x1, y1, fill=color, tags=("agent", tag))

    def close(self) -> None:
        self.root.destroy()
