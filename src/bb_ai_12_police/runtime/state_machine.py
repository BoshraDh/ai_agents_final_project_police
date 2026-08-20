"""GamePhaseMachine: the legal-transition state machine for one turn cycle
(book ch.8.3, "Orchestrator and State Machine" — reproduced near-verbatim
from the book's own example code, confirmed against the book text).

Rejecting any transition not listed in TRANSITIONS turns a logic bug into a
loud, immediate exception during development, instead of a silent deadlock
during a real match — the book's own stated reason for requiring this
table-driven design over ad hoc if/else phase tracking.
"""

from __future__ import annotations


class GamePhaseMachine:
    """Legal states for one turn cycle; illegal transitions raise immediately."""

    TRANSITIONS: dict[str, set[str]] = {
        "WAITING_FOR_OPPONENT": {"COMPUTING_MOVE"},
        "COMPUTING_MOVE": {"COMMITTING", "TECHNICAL_LOSS"},
        "COMMITTING": {"AWAITING_REVEAL"},
        "AWAITING_REVEAL": {"VERIFYING", "TECHNICAL_LOSS"},
        "VERIFYING": {"WAITING_FOR_OPPONENT"},
        "TECHNICAL_LOSS": set(),  # terminal state
    }

    def __init__(self) -> None:
        self.state = "WAITING_FOR_OPPONENT"

    def transition(self, target: str) -> str:
        """Reject any transition not listed in the table."""
        if target not in self.TRANSITIONS[self.state]:
            raise ValueError(f"Illegal transition: {self.state} -> {target}")
        self.state = target
        return self.state
