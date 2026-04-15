"""Forward validated multipart job requests to a full DocTranslater HTTP API."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from doctranslate.schemas.public_api import TranslationRequest
from pydantic import ValidationError
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)


async def _translation_request_json_from_form_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, UploadFile):
        body = await value.read()
        return body.decode("utf-8")
    if isinstance(value, bytes):
        return value.decode("utf-8")
    msg = f"Unexpected translation_request field type: {type(value)!r}"
    raise TypeError(msg)


async def validate_translation_request_multipart(
    form: Any,
) -> tuple[str, dict[str, str], UploadFile | None]:
    """Parse multipart form, validate ``translation_request`` JSON, return parts for upstream.

    Returns:
        Tuple of (translation_request_json_string, other_form_fields_as_strings, input_pdf_or_none).
    """
    tr_raw: str | None = None
    data: dict[str, str] = {}
    pdf: UploadFile | None = None

    for key, value in form.multi_items():
        if key == "input_pdf":
            if not isinstance(value, UploadFile):
                raise HTTPException(
                    status_code=400,
                    detail="input_pdf must be a file upload",
                )
            pdf = value
            continue
        if key == "translation_request":
            if tr_raw is not None:
                raise HTTPException(
                    status_code=400,
                    detail="duplicate translation_request field",
                )
            tr_raw = await _translation_request_json_from_form_value(value)
            continue
        if isinstance(value, UploadFile):
            raise HTTPException(
                status_code=400,
                detail=f"unexpected file field: {key!r}",
            )
        if key in data:
            raise HTTPException(
                status_code=400,
                detail=f"duplicate form field: {key!r}",
            )
        if isinstance(value, str):
            data[key] = value
        elif isinstance(value, bytes):
            data[key] = value.decode("utf-8")
        else:
            data[key] = str(value)

    if not tr_raw:
        raise HTTPException(
            status_code=400,
            detail="missing translation_request",
        )

    try:
        TranslationRequest.model_validate_json(tr_raw)
    except ValidationError as e:
        logger.debug("TranslationRequest validation failed: %s", e)
        raise HTTPException(status_code=400, detail=e.errors()) from e

    return tr_raw, data, pdf


async def forward_multipart_to_upstream(
    *,
    upstream_jobs_url: str,
    translation_request_json: str,
    extra_fields: dict[str, str],
    input_pdf: UploadFile | None,
    authorization: str | None,
    client: httpx.AsyncClient | None = None,
) -> httpx.Response:
    """POST the same multipart shape as ``POST /v1/jobs`` on the upstream API."""
    data: dict[str, str] = {
        "translation_request": translation_request_json,
        **extra_fields,
    }
    files: dict[str, Any] | None = None
    if input_pdf is not None:
        content = await input_pdf.read()
        files = {
            "input_pdf": (
                input_pdf.filename or "input.pdf",
                content,
                input_pdf.content_type or "application/pdf",
            ),
        }

    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization

    own_client = client is None
    c = client or httpx.AsyncClient(timeout=httpx.Timeout(120.0))
    try:
        post_kwargs: dict[str, Any] = {
            "data": data,
            "headers": headers,
        }
        if files is not None:
            post_kwargs["files"] = files
        return await c.post(upstream_jobs_url, **post_kwargs)
    finally:
        if own_client:
            await c.aclose()
