"""Stable public API for embedding DocTranslater in other applications.

Imports here pull the **full PDF + translator runtime** (install ``DocTranslater[full]``).
For configuration types only, use :mod:`doctranslate.schemas`.

Semantic versioning: treat symbols in ``__all__`` as public; deep imports under
``doctranslate.format.pdf`` are not guaranteed stable across minor releases.
"""

from __future__ import annotations

from doctranslate.format.pdf.high_level import async_translate
from doctranslate.format.pdf.high_level import translate
from doctranslate.format.pdf.translation_config import TranslateResult
from doctranslate.format.pdf.translation_config import TranslationConfig
from doctranslate.translator.factory import TranslatorBuildResult
from doctranslate.translator.factory import build_translators
from doctranslate.translator.factory import resolve_openai_api_key

__all__ = [
    "TranslateResult",
    "TranslationConfig",
    "TranslatorBuildResult",
    "async_translate",
    "build_translators",
    "resolve_openai_api_key",
    "translate",
]
