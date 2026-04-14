"""A client library for accessing DocTranslater HTTP API"""

from .client import AuthenticatedClient, Client
from .convenience import (
    download_artifact_bytes_async,
    download_artifact_bytes_sync,
    head_artifact_async,
    head_artifact_sync,
    iter_progress_events_async,
    iter_progress_events_sync,
    stream_job_sse_async,
    stream_job_sse_sync,
    wait_until_terminal_async,
    wait_until_terminal_sync,
)

__all__ = (
    "AuthenticatedClient",
    "Client",
    "download_artifact_bytes_async",
    "download_artifact_bytes_sync",
    "head_artifact_async",
    "head_artifact_sync",
    "iter_progress_events_async",
    "iter_progress_events_sync",
    "stream_job_sse_async",
    "stream_job_sse_sync",
    "wait_until_terminal_async",
    "wait_until_terminal_sync",
)
