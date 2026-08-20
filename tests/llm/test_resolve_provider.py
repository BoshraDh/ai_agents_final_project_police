"""Tests for the `[trash_talk]` config-driven provider factory."""

from __future__ import annotations

import pytest

from bb_ai_12_police.llm.resolve_provider import resolve_provider
from bb_ai_12_police.llm.template_provider import TemplateProvider

_SHARED = {"world": {"hint_max_words": 15}}


def test_resolve_provider_defaults_to_template():
    provider = resolve_provider({}, _SHARED)
    assert isinstance(provider, TemplateProvider)
    assert provider.hint_max_words == 15


def test_resolve_provider_reads_the_configured_name():
    provider = resolve_provider({"trash_talk": {"provider": "template"}}, _SHARED)
    assert isinstance(provider, TemplateProvider)


def test_resolve_provider_raises_for_an_unimplemented_provider():
    with pytest.raises(NotImplementedError):
        resolve_provider({"trash_talk": {"provider": "claude_api"}}, _SHARED)
