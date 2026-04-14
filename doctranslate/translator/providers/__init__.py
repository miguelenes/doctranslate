"""LLM provider adapters."""

from __future__ import annotations

from typing import Any

__all__ = ["LiteLLMProviderExecutor"]


def __getattr__(name: str) -> Any:
    if name == "LiteLLMProviderExecutor":
        from doctranslate.translator.providers.litellm_provider import (
            LiteLLMProviderExecutor,
        )

        return LiteLLMProviderExecutor
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
