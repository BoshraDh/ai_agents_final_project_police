"""Tests for the `[strategy]` config-driven brain factory."""

from __future__ import annotations

from bb_ai_12_police.strategy.police_brain import PoliceBrain
from bb_ai_12_police.strategy.resolve_brain import resolve_brain


def test_resolve_brain_defaults_to_police_brain_when_unset():
    brain = resolve_brain({})
    assert isinstance(brain, PoliceBrain)


def test_resolve_brain_loads_the_configured_class_path():
    private_config = {
        "strategy": {"police_class": "bb_ai_12_police.strategy.police_brain:PoliceBrain"}
    }
    brain = resolve_brain(private_config)
    assert isinstance(brain, PoliceBrain)
