"""Translation backends and multi-provider routing."""

from doctranslate.translator.config import NestedTranslatorConfig
from doctranslate.translator.config import load_nested_translator_config
from doctranslate.translator.config import validate_router_config
from doctranslate.translator.factory import build_translators
from doctranslate.translator.local_config import (
    convert_local_translator_to_router_nested,
)
from doctranslate.translator.local_config import local_cli_dict_from_args
from doctranslate.translator.local_config import merge_local_cli_into_nested
from doctranslate.translator.local_config import validate_local_nested
from doctranslate.translator.router import TranslatorRouter
from doctranslate.translator.translator import BaseTranslator
from doctranslate.translator.translator import OpenAITranslator
from doctranslate.translator.translator import TranslationError
from doctranslate.translator.translator import set_translate_rate_limiter
from doctranslate.translator.types import FailureCategory
from doctranslate.translator.types import RouterStrategy
from doctranslate.translator.types import TranslatorCapabilities

__all__ = [
    "BaseTranslator",
    "NestedTranslatorConfig",
    "OpenAITranslator",
    "RouterStrategy",
    "FailureCategory",
    "TranslatorCapabilities",
    "TranslationError",
    "TranslatorRouter",
    "build_translators",
    "load_nested_translator_config",
    "set_translate_rate_limiter",
    "validate_router_config",
    "convert_local_translator_to_router_nested",
    "local_cli_dict_from_args",
    "merge_local_cli_into_nested",
    "validate_local_nested",
]
