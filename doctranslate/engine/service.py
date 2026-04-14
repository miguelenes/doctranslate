"""Stable engine orchestration for public API and JSON CLI."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from doctranslate.engine.adapters import load_glossaries_from_request
from doctranslate.engine.adapters import translation_config_from_request
from doctranslate.exceptions import PriorTranslatedInputError
from doctranslate.format.pdf import high_level
from doctranslate.schemas.enums import PublicErrorCode
from doctranslate.schemas.public_api import InputFileInspection
from doctranslate.schemas.public_api import InputInspectionResult
from doctranslate.schemas.public_api import TranslationErrorPayload
from doctranslate.schemas.public_api import TranslationRequest
from doctranslate.schemas.public_api import TranslationResult
from doctranslate.schemas.public_api import progress_event_from_dict
from doctranslate.schemas.public_api import translation_result_from_runtime

logger = logging.getLogger(__name__)


def validate_request(data: dict[str, Any] | str | Path) -> TranslationRequest:
    """Parse and validate a :class:`~doctranslate.schemas.public_api.TranslationRequest`."""
    if isinstance(data, (str, Path)):
        raw = json.loads(Path(data).expanduser().read_text(encoding="utf-8"))
    else:
        raw = data
    return TranslationRequest.model_validate(raw)


def inspect_input(paths: list[str | Path]) -> InputInspectionResult:
    """Lightweight PDF inspection (page counts, prior-translation marker)."""
    import pymupdf

    files: list[InputFileInspection] = []
    for p in paths:
        fp = Path(p).expanduser()
        if not fp.is_file():
            msg = f"Not a file: {fp}"
            raise FileNotFoundError(msg)
        doc = pymupdf.open(fp)
        try:
            n = doc.page_count
            try:
                high_level.check_metadata(doc)
                prior: bool | None = False
            except PriorTranslatedInputError:
                prior = True
        finally:
            doc.close()
        files.append(
            InputFileInspection(
                path=str(fp.resolve()),
                page_count=n,
                prior_translated_marker=prior,
            ),
        )
    return InputInspectionResult(files=files)


def _exception_to_payload(exc: BaseException) -> TranslationErrorPayload:
    if isinstance(exc, asyncio.CancelledError):
        return TranslationErrorPayload(
            code=PublicErrorCode.CANCELED,
            message="Translation was canceled.",
            retryable=False,
        )
    if isinstance(exc, PriorTranslatedInputError):
        return TranslationErrorPayload(
            code=PublicErrorCode.INPUT_ERROR,
            message=str(exc),
            retryable=False,
            details={"reason": "prior_translated_input"},
        )
    if isinstance(exc, FileNotFoundError):
        return TranslationErrorPayload(
            code=PublicErrorCode.NOT_FOUND,
            message=str(exc),
            retryable=False,
        )
    if isinstance(exc, ValueError):
        return TranslationErrorPayload(
            code=PublicErrorCode.VALIDATION_ERROR,
            message=str(exc),
            retryable=False,
        )
    return TranslationErrorPayload(
        code=PublicErrorCode.INTERNAL_ERROR,
        message=str(exc),
        retryable=False,
        details={"exception_type": type(exc).__name__},
    )


def _default_doc_layout_model() -> Any:
    from doctranslate.docvision.doclayout import DocLayoutModel

    return DocLayoutModel.load_onnx()


def translate_job(request: TranslationRequest) -> TranslationResult:
    """Run a synchronous translation job from a public request."""
    glossaries = load_glossaries_from_request(request)
    doc_layout_model = _default_doc_layout_model()
    config = translation_config_from_request(
        request,
        glossaries=glossaries,
        doc_layout_model=doc_layout_model,
    )
    nop = getattr(doc_layout_model, "init_font_mapper", lambda _c: None)
    nop(config)
    try:
        raw = high_level.translate(config)
    except Exception:
        logger.exception("translate_job failed")
        raise
    try:
        config.run_tm_export_if_configured()
    except Exception:
        logger.exception("TM export failed (ignored for result)")
    return translation_result_from_runtime(raw)


async def async_translate_job(
    request: TranslationRequest,
) -> AsyncIterator[dict[str, Any]]:
    """Async progress stream with versioned, JSON-serializable event dicts."""
    glossaries = load_glossaries_from_request(request)
    doc_layout_model = _default_doc_layout_model()
    config = translation_config_from_request(
        request,
        glossaries=glossaries,
        doc_layout_model=doc_layout_model,
    )
    nop = getattr(doc_layout_model, "init_font_mapper", lambda _c: None)
    nop(config)
    try:
        async for raw in high_level.async_translate(config):
            try:
                yield progress_event_from_dict(dict(raw))
            except Exception as exc:
                logger.exception("Failed to normalize progress event")
                yield progress_event_from_dict(
                    {
                        "type": "error",
                        "error": TranslationErrorPayload(
                            code=PublicErrorCode.INTERNAL_ERROR,
                            message=f"Invalid progress event: {exc}",
                            details={
                                "raw_keys": list(raw.keys())
                                if isinstance(raw, dict)
                                else [],
                            },
                        ),
                    },
                )
                break
            if raw.get("type") == "finish":
                try:
                    config.run_tm_export_if_configured()
                except Exception:
                    logger.exception("TM export failed after finish")
                break
            if raw.get("type") == "error":
                break
    except asyncio.CancelledError:
        yield progress_event_from_dict(
            {
                "type": "error",
                "error": TranslationErrorPayload(
                    code=PublicErrorCode.CANCELED,
                    message="Canceled",
                ),
            },
        )
        raise
    except Exception as exc:
        logger.exception("async_translate_job failed")
        err = _exception_to_payload(exc)
        yield progress_event_from_dict({"type": "error", "error": err})


def translate_job_safe(
    request: TranslationRequest,
) -> TranslationResult | TranslationErrorPayload:
    """Like :func:`translate_job` but never raises for expected failures."""
    try:
        return translate_job(request)
    except Exception as exc:
        return _exception_to_payload(exc)
