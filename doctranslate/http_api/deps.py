"""FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi import Request

from doctranslate.http_api.job_manager import JobManager
from doctranslate.http_api.settings import ApiSettings
from doctranslate.http_api.settings import get_settings


def get_job_manager(request: Request) -> JobManager:
    """Return the process-wide :class:`JobManager` from app state."""
    return request.app.state.job_manager


JobManagerDep = Annotated[JobManager, Depends(get_job_manager)]
SettingsDep = Annotated[ApiSettings, Depends(get_settings)]
