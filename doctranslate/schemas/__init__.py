"""Typed configuration models with minimal third-party imports (schemas profile).

Prefer importing from this package for config validation in external apps.
Heavy PDF, LLM, and OCR stacks are *not* imported here.
"""

from __future__ import annotations

from doctranslate.format.pdf.translation_settings import TranslationSettings
from doctranslate.format.pdf.translation_settings import WatermarkOutputMode
from doctranslate.translator.config import NestedTranslatorConfig
from doctranslate.translator.config import ProviderConfigModel
from doctranslate.translator.config import RouteProfileConfig
from doctranslate.translator.config import load_nested_translator_config
from doctranslate.translator.config import merge_cli_router_overrides_from_mapping
from doctranslate.translator.config import resolve_provider_api_key
from doctranslate.translator.config import validate_router_config
from doctranslate.translator.types import FailureCategory
from doctranslate.translator.types import LLMOutputMode
from doctranslate.translator.types import LLMTransportKind
from doctranslate.translator.types import RouterStrategy
from doctranslate.translator.types import TokenUsage
from doctranslate.translator.types import TranslatorCapabilities

__all__ = [
    "FailureCategory",
    "LLMOutputMode",
    "LLMTransportKind",
    "NestedTranslatorConfig",
    "ProviderConfigModel",
    "RouteProfileConfig",
    "RouterStrategy",
    "TokenUsage",
    "TranslatorCapabilities",
    "TranslationSettings",
    "WatermarkOutputMode",
    "load_nested_translator_config",
    "merge_cli_router_overrides_from_mapping",
    "resolve_provider_api_key",
    "validate_router_config",
]
