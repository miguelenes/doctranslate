"""Stable public API for embedding DocTranslater in other applications.

Imports here pull the **full PDF + translator runtime** (install ``DocTranslater[full]``).
For configuration types only, use :mod:`doctranslate.schemas`.

Semantic versioning:

- Symbols listed in ``__all__`` are public and follow semver.
- :mod:`doctranslate.engine` and :mod:`doctranslate.pdf` are compatibility aliases; prefer this module.
- Deep imports under ``doctranslate.format.pdf`` are not guaranteed stable across minor releases.
- :mod:`doctranslate.experimental` has no stability guarantees.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from typing import overload

from doctranslate.engine import service as _engine_service
from doctranslate.format.pdf.high_level import (
    async_translate as _async_translate_legacy,
)
from doctranslate.format.pdf.high_level import translate as _translate_legacy
from doctranslate.format.pdf.translation_config import TranslateResult
from doctranslate.format.pdf.translation_config import TranslationConfig
from doctranslate.schemas.public_api import InputInspectionResult
from doctranslate.schemas.public_api import TranslationRequest
from doctranslate.schemas.public_api import TranslationResult
from doctranslate.schemas.versions import PUBLIC_SCHEMA_VERSION
from doctranslate.translator.factory import TranslatorBuildResult
from doctranslate.translator.factory import build_translators
from doctranslate.translator.factory import resolve_openai_api_key


@overload
def translate(translation_config: TranslationConfig) -> TranslateResult: ...


@overload
def translate(translation_config: TranslationRequest) -> TranslationResult: ...


def translate(translation_config: TranslationConfig | TranslationRequest) -> Any:
    """Translate a PDF using either a legacy :class:`TranslationConfig` or a :class:`TranslationRequest`."""
    if isinstance(translation_config, TranslationRequest):
        return _engine_service.translate_job(translation_config)
    return _translate_legacy(translation_config)


@overload
def async_translate(
    translation_config: TranslationConfig,
) -> AsyncIterator[dict[str, Any]]: ...


@overload
def async_translate(
    translation_config: TranslationRequest,
) -> AsyncIterator[dict[str, Any]]: ...


async def async_translate(
    translation_config: TranslationConfig | TranslationRequest,
) -> AsyncIterator[dict[str, Any]]:
    """Async progress API.

    For :class:`~doctranslate.schemas.public_api.TranslationRequest`, yields
    versioned JSON-serializable dicts (``schema_version`` / ``event_version`` on each event).

    For legacy :class:`~doctranslate.format.pdf.translation_config.TranslationConfig`,
    yields the historical event dict shape (including ``finish`` → ``translate_result``).
    """
    if isinstance(translation_config, TranslationRequest):
        async for ev in _engine_service.async_translate_job(translation_config):
            yield ev
        return
    # Legacy TranslationConfig: preserve the historical event dict shape (incl. finish.translate_result).
    async for raw in _async_translate_legacy(translation_config):
        yield dict(raw)


def validate_request(data: dict[str, Any] | str | Path) -> TranslationRequest:
    """Validate a JSON/dict payload and return a :class:`TranslationRequest`."""
    return _engine_service.validate_request(data)


def inspect_input(paths: list[str | Path]) -> InputInspectionResult:
    """Inspect PDF paths (page counts, prior-translation marker)."""
    return _engine_service.inspect_input(paths)


__all__ = [
    "PUBLIC_SCHEMA_VERSION",
    "TranslateResult",
    "TranslationConfig",
    "TranslationRequest",
    "TranslationResult",
    "TranslatorBuildResult",
    "async_translate",
    "build_translators",
    "inspect_input",
    "resolve_openai_api_key",
    "translate",
    "validate_request",
]
