"""Zero-token default trash-talk provider — canned sentence bank only.

Ships as the default so a full game is completable and gradeable with no
API keys configured (NFR-8). `ollama`/`claude_api`/`claude_cli` providers
(later stages) implement the same `TrashTalkProvider` contract with a real
LLM call, but never choose the move either.
"""

from __future__ import annotations

from bb_ai_12_police.llm.provider_base import TrashTalkProvider

_POLICE_LINES = [
    "You can't hide forever.",
    "I can practically smell your trail from here.",
    "Nowhere left to run in this city.",
    "Every step you take leaves a trace.",
]


class TemplateProvider(TrashTalkProvider):
    """Cycles a fixed, police-flavored sentence bank — zero LLM tokens."""

    def _generate(self, turn: int) -> str:
        return _POLICE_LINES[turn % len(_POLICE_LINES)]
