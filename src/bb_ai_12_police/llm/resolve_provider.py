"""Factory: resolve the trash-talk provider from `[trash_talk]` config.

Only `template` (0 tokens) is implemented in stage 4 — it's also the
required zero-LLM default (NFR-8). `ollama`/`claude_api`/`claude_cli` are
valid values in `config/game.toml` but raise `NotImplementedError` here
until a later stage wires the real HTTP/CLI calls.
"""

from __future__ import annotations

from typing import Any

from bb_ai_12_police.llm.provider_base import TrashTalkProvider
from bb_ai_12_police.llm.template_provider import TemplateProvider

_IMPLEMENTED = {"template": TemplateProvider}


def resolve_provider(
    private_config: dict[str, Any], shared_config: dict[str, Any]
) -> TrashTalkProvider:
    provider_name = private_config.get("trash_talk", {}).get("provider", "template")
    hint_max_words = shared_config["world"]["hint_max_words"]
    provider_cls = _IMPLEMENTED.get(provider_name)
    if provider_cls is None:
        raise NotImplementedError(
            f"trash_talk provider {provider_name!r} not implemented yet "
            "(stage 4 ships 'template' only)"
        )
    return provider_cls(hint_max_words)
