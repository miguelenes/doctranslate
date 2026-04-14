"""Asset warmup jobs."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from doctranslate.http_api.auth import require_api_operator
from doctranslate.http_api.deps import JobServiceDep
from doctranslate.http_api.errors import http_error
from doctranslate.http_api.models import JobCreateResponse
from doctranslate.observability.context import get_request_id
from doctranslate.schemas.enums import PublicErrorCode
from doctranslate.schemas.public_api import TranslationErrorPayload

router = APIRouter(
    tags=["assets"],
    dependencies=[Depends(require_api_operator)],
)


@router.post(
    "/v1/assets/warmup",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_warmup(job_service: JobServiceDep) -> JobCreateResponse:
    try:
        job_id = await job_service.create_warmup_job()
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
        kind="warmup",
        state="queued",
        status_url=f"/v1/jobs/{job_id}",
    )
