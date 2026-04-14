"""Translation backends and multi-provider routing."""

from __future__ import annotations

from typing import Any

from doctranslate.translator.config import NestedTranslatorConfig
from doctranslate.translator.config import load_nested_translator_config
from doctranslate.translator.config import validate_router_config
from doctranslate.translator.types import FailureCategory
from doctranslate.translator.types import RouterStrategy
from doctranslate.translator.types import TranslatorCapabilities

__all__ = [
    "BaseTranslator",
    "FailureCategory",
    "NestedTranslatorConfig",
    "OpenAITranslator",
    "RouterStrategy",
    "TranslationError",
    "TranslatorCapabilities",
    "TranslatorRouter",
    "build_translators",
    "convert_local_translator_to_router_nested",
    "load_nested_translator_config",
    "local_cli_dict_from_args",
    "merge_local_cli_into_nested",
    "set_translate_rate_limiter",
    "validate_local_nested",
    "validate_router_config",
]


def __getattr__(name: str) -> Any:
    if name == "BaseTranslator":
        from doctranslate.translator.translator import BaseTranslator

        return BaseTranslator
    if name == "OpenAITranslator":
        from doctranslate.translator.translator import OpenAITranslator

        return OpenAITranslator
    if name == "TranslationError":
        from doctranslate.translator.translator import TranslationError

        return TranslationError
    if name == "set_translate_rate_limiter":
        from doctranslate.translator.translator import set_translate_rate_limiter

        return set_translate_rate_limiter
    if name == "TranslatorRouter":
        from doctranslate.translator.router import TranslatorRouter

        return TranslatorRouter
    if name == "build_translators":
        from doctranslate.translator.factory import build_translators

        return build_translators
    if name == "convert_local_translator_to_router_nested":
        from doctranslate.translator.local_config import (
            convert_local_translator_to_router_nested,
        )

        return convert_local_translator_to_router_nested
    if name == "local_cli_dict_from_args":
        from doctranslate.translator.local_config import local_cli_dict_from_args

        return local_cli_dict_from_args
    if name == "merge_local_cli_into_nested":
        from doctranslate.translator.local_config import merge_local_cli_into_nested

        return merge_local_cli_into_nested
    if name == "validate_local_nested":
        from doctranslate.translator.local_config import validate_local_nested

        return validate_local_nested
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
