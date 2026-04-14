"""PDF and intermediate layout (IL) pipeline namespace.

This package re-exports the implementation under ``doctranslate.format.pdf``.
Prefer :mod:`doctranslate.api` for a smaller, documented surface.
"""

from __future__ import annotations

from doctranslate.format.pdf.high_level import TRANSLATE_STAGES
from doctranslate.format.pdf.high_level import async_translate
from doctranslate.format.pdf.high_level import init
from doctranslate.format.pdf.high_level import translate
from doctranslate.format.pdf.translation_config import TranslateResult
from doctranslate.format.pdf.translation_config import TranslationConfig

__all__ = [
    "TRANSLATE_STAGES",
    "TranslateResult",
    "TranslationConfig",
    "async_translate",
    "init",
    "translate",
]
