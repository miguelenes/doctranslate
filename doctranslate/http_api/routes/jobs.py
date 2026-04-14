"""Translation jobs and artifacts."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import Request
from fastapi import UploadFile
from fastapi import status
from fastapi.responses import FileResponse
from pydantic import ValidationError

from doctranslate.http_api.deps import JobManagerDep
from doctranslate.http_api.deps import SettingsDep
from doctranslate.http_api.errors import http_error
from doctranslate.http_api.models import ArtifactLink
from doctranslate.http_api.models import JobCreateResponse
from doctranslate.http_api.models import JobResultResponse
from doctranslate.http_api.models import JobStatusResponse
from doctranslate.schemas.enums import ArtifactKind
from doctranslate.schemas.enums import PublicErrorCode
from doctranslate.schemas.public_api import TranslationErrorPayload

router = APIRouter(tags=["jobs"])


def _record_to_status(job_id: str, rec: dict[str, Any]) -> JobStatusResponse:
    return JobStatusResponse(
        job_id=job_id,
        kind=rec["kind"],
        state=rec["state"],
        created_at=rec["created_at"],
        updated_at=rec["updated_at"],
        progress=rec.get("progress"),
        error=rec.get("error"),
        message=rec.get("message"),
    )


@router.post(
    "/v1/jobs",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_job(
    request: Request,
    settings: SettingsDep,
    job_manager: JobManagerDep,
    translation_request: str = Form(
        ...,
        description="JSON string of TranslationRequest",
    ),
    input_pdf: UploadFile | None = File(default=None),  # noqa: B008
) -> JobCreateResponse:
    from doctranslate.api import validate_request

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
        ) from e

    if input_pdf is not None:
        job_id = str(uuid.uuid4())
        paths = job_manager.store.job_paths(job_id)
        paths.mkdirs()
        dest = paths.input_dir / (input_pdf.filename or "input.pdf")
        if dest.suffix.lower() != ".pdf":
            dest = dest.with_suffix(".pdf")
        size = 0
        chunk_size = 1024 * 1024
        try:
            with dest.open("wb") as out:
                while True:
                    chunk = await input_pdf.read(chunk_size)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > settings.max_upload_bytes:
                        raise ValueError(
                            f"Upload exceeds max_upload_bytes={settings.max_upload_bytes}",
                        )
                    out.write(chunk)
        except ValueError as e:
            if "max_upload_bytes" in str(e):
                raise http_error(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    error=TranslationErrorPayload(
                        code=PublicErrorCode.VALIDATION_ERROR,
                        message=str(e),
                        retryable=False,
                    ),
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
            ) from e
        try:
            await job_manager.create_translation_job(
                req,
                input_pdf_path=dest,
                job_id=job_id,
            )
        except RuntimeError:
            raise http_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                error=TranslationErrorPayload(
                    code=PublicErrorCode.INTERNAL_ERROR,
                    message="Server busy; too many active or queued jobs.",
                    retryable=True,
                ),
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
        )
    path = Path(raw_path)
    err = job_manager.validate_mounted_input(path)
    if err is not None:
        raise http_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            error=err,
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
        ) from e
    try:
        job_id = await job_manager.create_translation_job(req, input_pdf_path=path)
    except RuntimeError:
        raise http_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error=TranslationErrorPayload(
                code=PublicErrorCode.INTERNAL_ERROR,
                message="Server busy; too many active or queued jobs.",
                retryable=True,
            ),
        ) from None
    return JobCreateResponse(
        job_id=job_id,
        kind="translation",
        state="queued",
        status_url=str(request.url_for("get_job", job_id=job_id)),
    )


@router.get("/v1/jobs/{job_id}", response_model=JobStatusResponse, name="get_job")
async def get_job(job_id: str, job_manager: JobManagerDep) -> JobStatusResponse:
    rec = await job_manager.get_record(job_id)
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown job")
    return _record_to_status(job_id, rec)


@router.post("/v1/jobs/{job_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_job(job_id: str, job_manager: JobManagerDep) -> None:
    rec = await job_manager.get_record(job_id)
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown job")
    await job_manager.cancel(job_id)


@router.get("/v1/jobs/{job_id}/result", response_model=JobResultResponse)
async def get_job_result(
    request: Request,
    job_id: str,
    job_manager: JobManagerDep,
) -> JobResultResponse:
    rec = await job_manager.get_record(job_id)
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown job")
    base = str(request.base_url).rstrip("/")
    artifacts: list[ArtifactLink] = []
    result = rec.get("result")
    if result is not None:
        for item in result.artifacts.items:
            url = f"{base}/v1/jobs/{job_id}/artifacts/{item.kind.value}"
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


@router.get("/v1/jobs/{job_id}/artifacts/{kind}")
async def download_artifact(
    job_id: str,
    kind: ArtifactKind,
    job_manager: JobManagerDep,
) -> FileResponse:
    rec = await job_manager.get_record(job_id)
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown job")
    result = rec.get("result")
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job has no result yet",
        )
    path: Path | None = None
    media = "application/octet-stream"
    for item in result.artifacts.items:
        if item.kind == kind:
            path = Path(item.path)
            media = item.media_type or media
            break
    if path is None or not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found"
        )
    return FileResponse(path, filename=path.name, media_type=media)
