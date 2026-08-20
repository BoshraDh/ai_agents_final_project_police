"""Police's default brain: pursue — minimize distance to the tracked thief."""

from __future__ import annotations

from bb_ai_12_police.strategy.heuristic_brain import HeuristicBrain


class PoliceBrain(HeuristicBrain):
    """Minimizes Manhattan distance to the tracked thief position (chases)."""

    _sign = 1
