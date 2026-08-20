"""Tests for the zero-token template trash-talk provider."""

from __future__ import annotations

from bb_ai_12_police.llm.template_provider import TemplateProvider


def test_hint_never_exceeds_hint_max_words():
    provider = TemplateProvider(hint_max_words=3)
    for turn in range(10):
        assert len(provider.hint(turn).split()) <= 3


def test_hint_is_deterministic_and_nonempty():
    provider = TemplateProvider(hint_max_words=15)
    first = provider.hint(0)
    assert first
    assert provider.hint(0) == first
