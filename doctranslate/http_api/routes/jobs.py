"""Translation jobs and artifacts."""

from __future__ import annotations

import asyncio
import base64
import binascii
import json
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from typing import NoReturn

import fsspec.core
from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import Request
from fastapi import UploadFile
from fastapi import status
from fastapi.responses import FileResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from fastapi.responses import StreamingResponse
from fastapi.sse import EventSourceResponse
from fastapi.sse import ServerSentEvent
from pydantic import ValidationError

from doctranslate.http_api.auth import require_api_operator
from doctranslate.http_api.deps import JobServiceDep
from doctranslate.http_api.deps import SettingsDep
from doctranslate.http_api.errors import http_error
from doctranslate.http_api.job_progress_hub import JobProgressHub
from doctranslate.http_api.job_sse import job_progress_sse
from doctranslate.http_api.models import ArtifactLink
from doctranslate.http_api.models import JobCreateJsonBody
from doctranslate.http_api.models import JobCreateResponse
from doctranslate.http_api.models import JobEventItem
from doctranslate.http_api.models import JobEventsResponse
from doctranslate.http_api.models import JobManifestItem
from doctranslate.http_api.models import JobManifestResponse
from doctranslate.http_api.models import JobResultResponse
from doctranslate.http_api.models import JobStatusResponse
from doctranslate.http_api.presign import presign_gcs_url
from doctranslate.http_api.presign import presign_s3_get_url
from doctranslate.http_api.range_requests import parse_bytes_range
from doctranslate.http_api.webhook_delivery import validate_webhook_url
from doctranslate.observability.context import get_request_id
from doctranslate.schemas.enums import ArtifactKind
from doctranslate.schemas.enums import PublicErrorCode
from doctranslate.schemas.public_api import TranslationErrorPayload

router = APIRouter(
    tags=["jobs"],
    dependencies=[Depends(require_api_operator)],
)


def _unknown_job_http() -> NoReturn:
    raise http_error(
        status_code=status.HTTP_404_NOT_FOUND,
        error=TranslationErrorPayload(
            code=PublicErrorCode.NOT_FOUND,
            message="Unknown job",
            retryable=False,
        ),
        request_id=get_request_id(),
    )


def _record_to_status(job_id: str, rec: dict[str, Any]) -> JobStatusResponse:
    return JobStatusResponse(
        job_id=job_id,
        kind=rec["kind"],
        state=rec["state"],
        created_at=rec["created_at"],
        updated_at=rec["updated_at"],
        progress=rec.get("progress"),
        progress_seq=int(rec.get("progress_seq") or 0),
        error=rec.get("error"),
        message=rec.get("message"),
    )


def _artifact_download_link(
    *,
    request: Request,
    job_id: str,
    item: Any,
    settings: Any,
) -> str:
    base = str(request.base_url).rstrip("/")
    if settings.artifact_download_mode == "redirect":
        path_str = item.path
        if path_str.startswith("s3://"):
            signed = presign_s3_get_url(
                path_str,
                expires_in=settings.presign_expires_seconds,
            )
            if signed:
                return signed
        if path_str.startswith("gs://") or path_str.startswith("gcs://"):
            signed = presign_gcs_url(
                path_str,
                expires_in=settings.presign_expires_seconds,
            )
            if signed:
                return signed
    return f"{base}/v1/jobs/{job_id}/artifacts/{item.kind.value}"


def _artifact_filename(kind: ArtifactKind) -> str:
    if kind == ArtifactKind.AUTO_EXTRACTED_GLOSSARY_CSV:
        return "glossary.csv"
    return f"{kind.value}.pdf"


def _validate_webhook_mapping(
    cfg: dict[str, Any],
    settings: Any,
) -> dict[str, Any]:
    url = cfg.get("url")
    if not isinstance(url, str) or not url.strip():
        msg = "webhook.url is required"
        raise ValueError(msg)
    validate_webhook_url(url.strip(), settings=settings)
    out = dict(cfg)
    out["url"] = url.strip()
    return out


def _parse_job_webhook(
    raw: str | None,
    settings: Any,
) -> dict[str, Any] | None:
    if raw is None or not str(raw).strip():
        return None
    try:
        cfg = json.loads(raw)
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON in webhook field: {e}"
        raise ValueError(msg) from e
    if not isinstance(cfg, dict):
        msg = "webhook must be a JSON object"
        raise TypeError(msg)
    return _validate_webhook_mapping(cfg, settings)


@router.post(
    "/v1/jobs",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    operation_id="v1_jobs_create_multipart",
)
async def create_job(
    request: Request,
    settings: SettingsDep,
    job_service: JobServiceDep,
    translation_request: str = Form(
        ...,
        description="JSON string of TranslationRequest",
    ),
    input_pdf: UploadFile | None = File(default=None),  # noqa: B008
    webhook: str | None = Form(
        default=None,
        description='Optional JSON object: {"url":"https://...","secret":"..."} or secret_env.',
    ),
) -> JobCreateResponse:
    from doctranslate.api import validate_request

    try:
        wh_cfg = _parse_job_webhook(webhook, settings)
    except (TypeError, ValueError) as e:
        raise http_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            error=TranslationErrorPayload(
                code=PublicErrorCode.VALIDATION_ERROR,
                message=str(e),
                retryable=False,
            ),
            request_id=get_request_id(),
        ) from e

    try:
        data: dict[str, Any] = json.loads(translation_request)
    except json.JSONDecodeError as e:
        raise http_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            error=TranslationErrorPayload(
                code=PublicErrorCode.VALIDATION_ERROR,
                message=f"Invalid JSON in translation_request field: {e}",
                retryable=False,
            ),
            request_id=get_request_id(),
        ) from e

    if input_pdf is not None:
        job_id = str(uuid.uuid4())
        job_service.artifact_store.ensure_workspace(job_id)

        async def read_chunk(n: int) -> bytes:
            return await input_pdf.read(n)

        try:
            dest = await job_service.artifact_store.save_uploaded_input(
                job_id,
                input_pdf.filename,
                settings.max_upload_bytes,
                read_chunk,
            )
        except ValueError as e:
            if "max_upload_bytes" in str(e):
                raise http_error(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    error=TranslationErrorPayload(
                        code=PublicErrorCode.VALIDATION_ERROR,
                        message=str(e),
                        retryable=False,
                    ),
                    request_id=get_request_id(),
                ) from e
            raise
        except OSError as e:
            raise http_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error=TranslationErrorPayload(
                    code=PublicErrorCode.INTERNAL_ERROR,
                    message=str(e),
                    retryable=False,
                ),
                request_id=get_request_id(),
            ) from e

        merged = {**data, "input_pdf": str(dest.resolve())}
        try:
            req = validate_request(merged)
        except (ValidationError, ValueError, TypeError, OSError) as e:
            raise http_error(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error=TranslationErrorPayload(
                    code=PublicErrorCode.VALIDATION_ERROR,
                    message=str(e),
                    retryable=False,
                ),
                request_id=get_request_id(),
            ) from e
        try:
            await job_service.create_translation_job(
                req,
                input_pdf_path=dest,
                job_id=job_id,
                webhook=wh_cfg,
            )
        except RuntimeError:
            raise http_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                error=TranslationErrorPayload(
                    code=PublicErrorCode.INTERNAL_ERROR,
                    message="Server busy; too many active or queued jobs.",
                    retryable=True,
                ),
                request_id=get_request_id(),
            ) from None
        return JobCreateResponse(
            job_id=job_id,
            kind="translation",
            state="queued",
            status_url=str(request.url_for("get_job", job_id=job_id)),
        )

    raw_path = data.get("input_pdf")
    if not raw_path or not isinstance(raw_path, str):
        raise http_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            error=TranslationErrorPayload(
                code=PublicErrorCode.VALIDATION_ERROR,
                message="input_pdf is required when no file upload is provided",
                retryable=False,
            ),
            request_id=get_request_id(),
        )
    path = Path(raw_path)
    err = job_service.validate_mounted_input(path)
    if err is not None:
        raise http_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            error=err,
            request_id=get_request_id(),
        )
    try:
        req = validate_request(data)
    except (ValidationError, ValueError, TypeError, OSError) as e:
        raise http_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error=TranslationErrorPayload(
                code=PublicErrorCode.VALIDATION_ERROR,
                message=str(e),
                retryable=False,
            ),
            request_id=get_request_id(),
        ) from e
    try:
        job_id = await job_service.create_translation_job(
            req,
            input_pdf_path=path,
            webhook=wh_cfg,
        )
    except RuntimeError:
        raise http_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error=TranslationErrorPayload(
                code=PublicErrorCode.INTERNAL_ERROR,
                message="Server busy; too many active or queued jobs.",
                retryable=True,
            ),
            request_id=get_request_id(),
        ) from None
    return JobCreateResponse(
        job_id=job_id,
        kind="translation",
        state="queued",
        status_url=str(request.url_for("get_job", job_id=job_id)),
    )


@router.post(
    "/v1/jobs/json",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    operation_id="v1_jobs_create_json",
)
async def create_job_json(
    request: Request,
    settings: SettingsDep,
    job_service: JobServiceDep,
    body: JobCreateJsonBody,
) -> JobCreateResponse:
    """Create a translation job from a typed JSON body (OpenAPI-friendly)."""
    from doctranslate.api import validate_request

    wh_cfg: dict[str, Any] | None = None
    if body.webhook is not None:
        try:
            wh_cfg = _validate_webhook_mapping(
                body.webhook.model_dump(mode="json", exclude_none=True),
                settings,
            )
        except (TypeError, ValueError) as e:
            raise http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                error=TranslationErrorPayload(
                    code=PublicErrorCode.VALIDATION_ERROR,
                    message=str(e),
                    retryable=False,
                ),
                request_id=get_request_id(),
            ) from e

    if body.input_pdf_base64 is not None:
        try:
            raw_pdf = base64.standard_b64decode(body.input_pdf_base64)
        except (binascii.Error, ValueError) as e:
            raise http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                error=TranslationErrorPayload(
                    code=PublicErrorCode.VALIDATION_ERROR,
                    message=f"Invalid base64 in input_pdf_base64: {e}",
                    retryable=False,
                ),
                request_id=get_request_id(),
            ) from e
        job_id = str(uuid.uuid4())
        job_service.artifact_store.ensure_workspace(job_id)

        class _OneShotUpload:
            __slots__ = ("_buf", "_done")

            def __init__(self, buf: bytes) -> None:
                self._buf = buf
                self._done = False

            async def read_chunk(self, _n: int) -> bytes:
                if self._done:
                    return b""
                self._done = True
                return self._buf

        uploader = _OneShotUpload(raw_pdf)

        try:
            dest = await job_service.artifact_store.save_uploaded_input(
                job_id,
                "input.pdf",
                settings.max_upload_bytes,
                uploader.read_chunk,
            )
        except ValueError as e:
            if "max_upload_bytes" in str(e):
                raise http_error(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    error=TranslationErrorPayload(
                        code=PublicErrorCode.VALIDATION_ERROR,
                        message=str(e),
                        retryable=False,
                    ),
                    request_id=get_request_id(),
                ) from e
            raise
        except OSError as e:
            raise http_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error=TranslationErrorPayload(
                    code=PublicErrorCode.INTERNAL_ERROR,
                    message=str(e),
                    retryable=False,
                ),
                request_id=get_request_id(),
            ) from e

        try:
            req = body.translation_request.model_copy(
                update={"input_pdf": str(dest.resolve())},
            )
            validate_request(req.model_dump(mode="json"))
        except (ValidationError, ValueError, TypeError, OSError) as e:
            raise http_error(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error=TranslationErrorPayload(
                    code=PublicErrorCode.VALIDATION_ERROR,
                    message=str(e),
                    retryable=False,
                ),
                request_id=get_request_id(),
            ) from e
        try:
            await job_service.create_translation_job(
                req,
                input_pdf_path=dest,
                job_id=job_id,
                webhook=wh_cfg,
            )
        except RuntimeError:
            raise http_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                error=TranslationErrorPayload(
                    code=PublicErrorCode.INTERNAL_ERROR,
                    message="Server busy; too many active or queued jobs.",
                    retryable=True,
                ),
                request_id=get_request_id(),
            ) from None
        return JobCreateResponse(
            job_id=job_id,
            kind="translation",
            state="queued",
            status_url=str(request.url_for("get_job", job_id=job_id)),
        )

    raw_path = body.translation_request.input_pdf
    if not raw_path or not str(raw_path).strip():
        raise http_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            error=TranslationErrorPayload(
                code=PublicErrorCode.VALIDATION_ERROR,
                message="input_pdf is required when input_pdf_base64 is omitted",
                retryable=False,
            ),
            request_id=get_request_id(),
        )
    path = Path(raw_path)
    err = job_service.validate_mounted_input(path)
    if err is not None:
        raise http_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            error=err,
            request_id=get_request_id(),
        )
    try:
        req = body.translation_request.model_copy(
            update={"input_pdf": str(path.resolve())},
        )
        validate_request(req.model_dump(mode="json"))
    except (ValidationError, ValueError, TypeError, OSError) as e:
        raise http_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error=TranslationErrorPayload(
                code=PublicErrorCode.VALIDATION_ERROR,
                message=str(e),
                retryable=False,
            ),
            request_id=get_request_id(),
        ) from e
    try:
        job_id = await job_service.create_translation_job(
            req,
            input_pdf_path=path,
            webhook=wh_cfg,
        )
    except RuntimeError:
        raise http_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error=TranslationErrorPayload(
                code=PublicErrorCode.INTERNAL_ERROR,
                message="Server busy; too many active or queued jobs.",
                retryable=True,
            ),
            request_id=get_request_id(),
        ) from None
    return JobCreateResponse(
        job_id=job_id,
        kind="translation",
        state="queued",
        status_url=str(request.url_for("get_job", job_id=job_id)),
    )


@router.get(
    "/v1/jobs/{job_id}",
    response_model=JobStatusResponse,
    name="get_job",
    operation_id="v1_jobs_get",
)
async def get_job(job_id: str, job_service: JobServiceDep) -> JobStatusResponse:
    rec = await job_service.get_record(job_id)
    if rec is None:
        _unknown_job_http()
    return _record_to_status(job_id, rec)


@router.get(
    "/v1/jobs/{job_id}/events",
    response_model=JobEventsResponse,
    operation_id="v1_jobs_events_list",
)
async def list_job_events(
    job_id: str,
    job_service: JobServiceDep,
    after_seq: int = 0,
    limit: int = 500,
) -> JobEventsResponse:
    rec = await job_service.get_record(job_id)
    if rec is None:
        _unknown_job_http()
    rows = job_service.list_job_events(job_id, after_seq=after_seq, limit=limit)
    return JobEventsResponse(
        job_id=job_id,
        items=[JobEventItem(seq=r["seq"], event=r["event"]) for r in rows],
    )


@router.get(
    "/v1/jobs/{job_id}/stream",
    response_class=EventSourceResponse,
    response_model=None,
    operation_id="v1_jobs_stream",
)
async def stream_job_progress(
    request: Request,
    job_id: str,
    job_service: JobServiceDep,
    settings: SettingsDep,
    full_events: bool = False,
) -> AsyncIterator[ServerSentEvent]:
    raw_hub = getattr(request.app.state, "job_progress_hub", None)
    hub = raw_hub if isinstance(raw_hub, JobProgressHub) else None
    async for ev in job_progress_sse(
        request=request,
        job_id=job_id,
        job_service=job_service,
        settings=settings,
        hub=hub,
        full_events=full_events,
    ):
        yield ev


@router.post(
    "/v1/jobs/{job_id}/cancel",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="v1_jobs_cancel",
)
async def cancel_job(job_id: str, job_service: JobServiceDep) -> None:
    rec = await job_service.get_record(job_id)
    if rec is None:
        _unknown_job_http()
    await job_service.cancel(job_id)


@router.get(
    "/v1/jobs/{job_id}/result",
    response_model=JobResultResponse,
    operation_id="v1_jobs_result_get",
)
async def get_job_result(
    request: Request,
    job_id: str,
    job_service: JobServiceDep,
    settings: SettingsDep,
) -> JobResultResponse:
    rec = await job_service.get_record(job_id)
    if rec is None:
        _unknown_job_http()
    artifacts: list[ArtifactLink] = []
    result = rec.get("result")
    if result is not None:
        for item in result.artifacts.items:
            url = _artifact_download_link(
                request=request,
                job_id=job_id,
                item=item,
                settings=settings,
            )
            artifacts.append(
                ArtifactLink(
                    kind=item.kind,
                    download_url=url,
                    path=item.path,
                    sha256=item.sha256,
                    size_bytes=item.size_bytes,
                ),
            )
    return JobResultResponse(
        job_id=job_id,
        kind=rec["kind"],
        state=rec["state"],
        translation_result=result,
        artifacts=artifacts,
        error=rec.get("error"),
    )


@router.get(
    "/v1/jobs/{job_id}/manifest",
    response_model=JobManifestResponse,
    operation_id="v1_jobs_manifest_get",
)
async def get_job_manifest(
    request: Request,
    job_id: str,
    job_service: JobServiceDep,
    settings: SettingsDep,
) -> JobManifestResponse:
    rec = await job_service.get_record(job_id)
    if rec is None:
        _unknown_job_http()
    if rec["state"] != "succeeded":
        raise http_error(
            status_code=status.HTTP_409_CONFLICT,
            error=TranslationErrorPayload(
                code=PublicErrorCode.INPUT_ERROR,
                message="Job has not succeeded yet",
                retryable=False,
            ),
            request_id=get_request_id(),
        )
    result = rec.get("result")
    if result is None:
        raise http_error(
            status_code=status.HTTP_404_NOT_FOUND,
            error=TranslationErrorPayload(
                code=PublicErrorCode.NOT_FOUND,
                message="Job has no result yet",
                retryable=False,
            ),
            request_id=get_request_id(),
        )
    items: list[JobManifestItem] = []
    exp = (
        int(settings.presign_expires_seconds)
        if settings.artifact_download_mode == "redirect"
        else None
    )
    for item in result.artifacts.items:
        url = _artifact_download_link(
            request=request,
            job_id=job_id,
            item=item,
            settings=settings,
        )
        items.append(
            JobManifestItem(
                kind=item.kind,
                download_url=url,
                path=item.path,
                sha256=item.sha256,
                size_bytes=item.size_bytes,
                media_type=item.media_type,
                filename=_artifact_filename(item.kind),
                download_expires_in_seconds=exp,
            ),
        )
    return JobManifestResponse(
        job_id=job_id,
        kind=rec["kind"],
        state=rec["state"],
        items=items,
    )


def _remote_file_size(url: str, opts: dict[str, Any]) -> int:
    fs, p = fsspec.core.url_to_fs(url, **opts)
    info = fs.info(p)
    return int(info.get("size") or info.get("Size") or 0)


@router.head(
    "/v1/jobs/{job_id}/artifacts/{kind}",
    response_model=None,
    operation_id="v1_jobs_artifact_head",
)
async def head_artifact(
    job_id: str,
    kind: ArtifactKind,
    job_service: JobServiceDep,
    settings: SettingsDep,
) -> Response:
    rec = await job_service.get_record(job_id)
    if rec is None:
        _unknown_job_http()
    result = rec.get("result")
    if result is None:
        raise http_error(
            status_code=status.HTTP_404_NOT_FOUND,
            error=TranslationErrorPayload(
                code=PublicErrorCode.NOT_FOUND,
                message="Job has no result yet",
                retryable=False,
            ),
            request_id=get_request_id(),
        )
    artifact = None
    media = "application/octet-stream"
    for item in result.artifacts.items:
        if item.kind == kind:
            artifact = item
            media = item.media_type or media
            break
    if artifact is None:
        raise http_error(
            status_code=status.HTTP_404_NOT_FOUND,
            error=TranslationErrorPayload(
                code=PublicErrorCode.NOT_FOUND,
                message="Artifact not found",
                retryable=False,
            ),
            request_id=get_request_id(),
        )
    if settings.artifact_download_mode == "redirect":
        path_str = artifact.path
        if (
            path_str.startswith("s3://")
            or path_str.startswith("gs://")
            or path_str.startswith("gcs://")
        ):
            return Response(
                status_code=status.HTTP_200_OK,
                headers={
                    "Content-Type": media,
                    "Accept-Ranges": "bytes",
                },
            )
    mode, payload = job_service.artifact_store.resolve_artifact_for_download(
        job_id,
        kind,
        artifact,
    )
    if mode == "path":
        path: Path = payload["path"]
        if not path.is_file():
            raise http_error(
                status_code=status.HTTP_404_NOT_FOUND,
                error=TranslationErrorPayload(
                    code=PublicErrorCode.NOT_FOUND,
                    message="Artifact not found",
                    retryable=False,
                ),
                request_id=get_request_id(),
            )
        size = path.stat().st_size
        return Response(
            status_code=status.HTTP_200_OK,
            headers={
                "Content-Length": str(size),
                "Content-Type": media,
                "Accept-Ranges": "bytes",
            },
        )
    if mode == "fsspec":
        url = payload["url"]
        opts = job_service.artifact_store.fsspec_read_options()
        try:
            fsize = await asyncio.to_thread(_remote_file_size, url, opts)
        except Exception:
            raise http_error(
                status_code=status.HTTP_404_NOT_FOUND,
                error=TranslationErrorPayload(
                    code=PublicErrorCode.NOT_FOUND,
                    message="Artifact not found",
                    retryable=False,
                ),
                request_id=get_request_id(),
            ) from None
        return Response(
            status_code=status.HTTP_200_OK,
            headers={
                "Content-Length": str(fsize),
                "Content-Type": media,
                "Accept-Ranges": "bytes",
            },
        )
    raise http_error(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error=TranslationErrorPayload(
            code=PublicErrorCode.INTERNAL_ERROR,
            message="Unknown artifact storage mode",
            retryable=False,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/v1/jobs/{job_id}/artifacts/{kind}",
    response_model=None,
    operation_id="v1_jobs_artifact_get",
)
async def download_artifact(
    request: Request,
    job_id: str,
    kind: ArtifactKind,
    job_service: JobServiceDep,
    settings: SettingsDep,
) -> Response:
    rec = await job_service.get_record(job_id)
    if rec is None:
        _unknown_job_http()
    result = rec.get("result")
    if result is None:
        raise http_error(
            status_code=status.HTTP_404_NOT_FOUND,
            error=TranslationErrorPayload(
                code=PublicErrorCode.NOT_FOUND,
                message="Job has no result yet",
                retryable=False,
            ),
            request_id=get_request_id(),
        )
    artifact = None
    media = "application/octet-stream"
    for item in result.artifacts.items:
        if item.kind == kind:
            artifact = item
            media = item.media_type or media
            break
    if artifact is None:
        raise http_error(
            status_code=status.HTTP_404_NOT_FOUND,
            error=TranslationErrorPayload(
                code=PublicErrorCode.NOT_FOUND,
                message="Artifact not found",
                retryable=False,
            ),
            request_id=get_request_id(),
        )

    if settings.artifact_download_mode == "redirect":
        path_str = artifact.path
        if path_str.startswith("s3://"):
            signed = presign_s3_get_url(
                path_str,
                expires_in=settings.presign_expires_seconds,
            )
            if signed:
                return RedirectResponse(url=signed, status_code=307)
        if path_str.startswith("gs://") or path_str.startswith("gcs://"):
            signed = presign_gcs_url(
                path_str,
                expires_in=settings.presign_expires_seconds,
            )
            if signed:
                return RedirectResponse(url=signed, status_code=307)

    mode, payload = job_service.artifact_store.resolve_artifact_for_download(
        job_id,
        kind,
        artifact,
    )
    filename = payload.get("filename") or "artifact.bin"
    range_header = request.headers.get("range")

    if mode == "path":
        path: Path = payload["path"]
        if not path.is_file():
            raise http_error(
                status_code=status.HTTP_404_NOT_FOUND,
                error=TranslationErrorPayload(
                    code=PublicErrorCode.NOT_FOUND,
                    message="Artifact not found",
                    retryable=False,
                ),
                request_id=get_request_id(),
            )
        size = path.stat().st_size
        pr = parse_bytes_range(range_header, size)
        if pr == "unsatisfiable":
            return Response(
                status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                headers={"Content-Range": f"bytes */{size}"},
            )
        if pr is None:
            return FileResponse(
                path,
                filename=filename,
                media_type=media,
                headers={"Accept-Ranges": "bytes"},
            )
        start, end = pr
        length = end - start + 1

        async def local_body() -> Any:
            with path.open("rb") as f:
                f.seek(start)
                remain = length
                while remain > 0:
                    chunk = await asyncio.to_thread(f.read, min(65536, remain))
                    if not chunk:
                        break
                    remain -= len(chunk)
                    yield chunk

        return StreamingResponse(
            local_body(),
            status_code=206,
            media_type=media,
            headers={
                "Content-Range": f"bytes {start}-{end}/{size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(length),
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    if mode == "fsspec":
        url = payload["url"]
        opts = job_service.artifact_store.fsspec_read_options()
        try:
            fsize = await asyncio.to_thread(_remote_file_size, url, opts)
        except Exception:
            raise http_error(
                status_code=status.HTTP_404_NOT_FOUND,
                error=TranslationErrorPayload(
                    code=PublicErrorCode.NOT_FOUND,
                    message="Artifact not found",
                    retryable=False,
                ),
                request_id=get_request_id(),
            ) from None
        pr = parse_bytes_range(range_header, fsize)
        if pr == "unsatisfiable":
            return Response(
                status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                headers={"Content-Range": f"bytes */{fsize}"},
            )

        if pr is None:

            def full_remote_sync() -> Any:
                with fsspec.open(url, "rb", **opts) as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk:
                            break
                        yield chunk

            return StreamingResponse(
                full_remote_sync(),
                media_type=media,
                headers={
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(fsize),
                    "Content-Disposition": f'attachment; filename="{filename}"',
                },
            )

        start, end = pr
        length = end - start + 1

        def ranged_remote_sync() -> Any:
            with fsspec.open(url, "rb", **opts) as f:
                f.seek(start)
                remain = length
                while remain > 0:
                    chunk = f.read(min(65536, remain))
                    if not chunk:
                        break
                    remain -= len(chunk)
                    yield chunk

        return StreamingResponse(
            ranged_remote_sync(),
            status_code=206,
            media_type=media,
            headers={
                "Content-Range": f"bytes {start}-{end}/{fsize}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(length),
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    raise http_error(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error=TranslationErrorPayload(
            code=PublicErrorCode.INTERNAL_ERROR,
            message="Unknown artifact storage mode",
            retryable=False,
        ),
        request_id=get_request_id(),
    )
