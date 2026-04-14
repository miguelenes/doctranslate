"""FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi import Request

from doctranslate.http_api.auth import require_api_operator
from doctranslate.http_api.auth import require_api_operator_when_probes_are_protected
from doctranslate.http_api.job_manager import JobManager
from doctranslate.http_api.job_service import HttpJobService
from doctranslate.http_api.settings import ApiSettings
from doctranslate.http_api.settings import get_settings


def get_job_manager(request: Request) -> JobManager:
    """Return the process-wide :class:`JobManager` from app state."""
    return request.app.state.job_manager


def get_job_service(request: Request) -> HttpJobService:
    """Return the process-wide :class:`HttpJobService` from app state."""
    return request.app.state.job_service


JobManagerDep = Annotated[JobManager, Depends(get_job_manager)]
JobServiceDep = Annotated[HttpJobService, Depends(get_job_service)]
SettingsDep = Annotated[ApiSettings, Depends(get_settings)]
RequireApiOperatorDep = Annotated[None, Depends(require_api_operator)]
RequireApiOperatorForProbesDep = Annotated[
    None,
    Depends(require_api_operator_when_probes_are_protected),
]
