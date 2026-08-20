"""Contract for trash-talk/hint text generation.

Book-binding rule: a provider generates TEXT ONLY. The move decision lives
entirely in `strategy/`; a provider is never consulted for a `Direction`.
`hint()` centralizes the `hint_max_words` cap so every provider — template
or a real LLM in a later stage — is truncated the same way.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class TrashTalkProvider(ABC):
    """Produces one short line of in-game banter/hint text per turn."""

    def __init__(self, hint_max_words: int) -> None:
        self.hint_max_words = hint_max_words

    @abstractmethod
    def _generate(self, turn: int) -> str:
        """Return raw text for this turn; may exceed the word cap."""

    def hint(self, turn: int) -> str:
        words = self._generate(turn).split()
        return " ".join(words[: self.hint_max_words])
