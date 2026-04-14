"""Map engine errors to HTTP responses."""

from __future__ import annotations

from fastapi import HTTPException

from doctranslate.schemas.public_api import TranslationErrorPayload


def http_error(
    *,
    status_code: int,
    error: TranslationErrorPayload,
    request_id: str | None = None,
) -> HTTPException:
    """Build an :class:`HTTPException` with a structured JSON body."""
    from doctranslate.http_api.models import ApiErrorEnvelope

    body = ApiErrorEnvelope(request_id=request_id, error=error).model_dump(
        mode="json",
    )
    return HTTPException(status_code=status_code, detail=body)
