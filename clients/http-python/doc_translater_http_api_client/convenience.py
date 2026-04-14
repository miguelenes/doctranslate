"""Small helpers on top of the generated OpenAPI client (poll, SSE, artifacts)."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from doc_translater_http_api_client.client import AuthenticatedClient, Client
    from doc_translater_http_api_client.models.job_events_response import JobEventsResponse
    from doc_translater_http_api_client.models.job_status_response import JobStatusResponse

logger = logging.getLogger(__name__)

_TERMINAL = frozenset({"succeeded", "failed", "canceled"})


def wait_until_terminal_sync(
    *,
    client: Client | AuthenticatedClient,
    job_id: str,
    poll_interval_s: float = 0.25,
    timeout_s: float | None = 600.0,
) -> JobStatusResponse:
    """Poll ``GET /v1/jobs/{job_id}`` until the job reaches a terminal state."""
    from doc_translater_http_api_client.api.jobs import v1_jobs_get

    deadline = None if timeout_s is None else time.monotonic() + timeout_s
    while True:
        resp = v1_jobs_get.sync_detailed(job_id=job_id, client=client)
        if resp.status_code != 200 or resp.parsed is None:
            msg = f"unexpected status polling job: {resp.status_code}"
            raise RuntimeError(msg)
        body = resp.parsed
        if body.state in _TERMINAL:
            return body
        if deadline is not None and time.monotonic() > deadline:
            msg = f"timeout waiting for job {job_id}"
            raise TimeoutError(msg)
        time.sleep(poll_interval_s)


async def wait_until_terminal_async(
    *,
    client: Client | AuthenticatedClient,
    job_id: str,
    poll_interval_s: float = 0.25,
    timeout_s: float | None = 600.0,
) -> JobStatusResponse:
    """Async variant of :func:`wait_until_terminal_sync`."""
    from doc_translater_http_api_client.api.jobs import v1_jobs_get

    deadline = None if timeout_s is None else time.monotonic() + timeout_s
    while True:
        resp = await v1_jobs_get.asyncio_detailed(job_id=job_id, client=client)
        if resp.status_code != 200 or resp.parsed is None:
            msg = f"unexpected status polling job: {resp.status_code}"
            raise RuntimeError(msg)
        body = resp.parsed
        if body.state in _TERMINAL:
            return body
        if deadline is not None and time.monotonic() > deadline:
            msg = f"timeout waiting for job {job_id}"
            raise TimeoutError(msg)
        await asyncio.sleep(poll_interval_s)


def iter_progress_events_sync(
    *,
    client: Client | AuthenticatedClient,
    job_id: str,
    after_seq: int = 0,
    page_limit: int = 200,
) -> Iterator[JobEventsResponse]:
    """Yield paginated ``GET /v1/jobs/{id}/events`` pages until an empty page."""
    from doc_translater_http_api_client.api.jobs import v1_jobs_events_list

    cursor = after_seq
    while True:
        resp = v1_jobs_events_list.sync_detailed(
            job_id=job_id,
            client=client,
            after_seq=cursor,
            limit=page_limit,
        )
        if resp.status_code != 200 or resp.parsed is None:
            msg = f"unexpected status listing events: {resp.status_code}"
            raise RuntimeError(msg)
        page = resp.parsed
        if not page.items:
            break
        yield page
        cursor = page.items[-1].seq


async def iter_progress_events_async(
    *,
    client: Client | AuthenticatedClient,
    job_id: str,
    after_seq: int = 0,
    page_limit: int = 200,
) -> AsyncIterator[JobEventsResponse]:
    """Async variant of :func:`iter_progress_events_sync`."""
    from doc_translater_http_api_client.api.jobs import v1_jobs_events_list

    cursor = after_seq
    while True:
        resp = await v1_jobs_events_list.asyncio_detailed(
            job_id=job_id,
            client=client,
            after_seq=cursor,
            limit=page_limit,
        )
        if resp.status_code != 200 or resp.parsed is None:
            msg = f"unexpected status listing events: {resp.status_code}"
            raise RuntimeError(msg)
        page = resp.parsed
        if not page.items:
            break
        yield page
        cursor = page.items[-1].seq


def stream_job_sse_sync(
    *,
    client: Client | AuthenticatedClient,
    job_id: str,
    full_events: bool = False,
) -> Iterator[dict[str, Any]]:
    """Parse ``GET /v1/jobs/{id}/stream`` (``text/event-stream``) into decoded ``data`` dicts."""
    hc = client.get_httpx_client()
    params = {"full_events": "1"} if full_events else {}
    url = f"/v1/jobs/{job_id}/stream"
    with hc.stream("GET", url, params=params, headers={"Accept": "text/event-stream"}) as stream:
        stream.raise_for_status()
        buf = ""
        for raw in stream.iter_text():
            buf += raw
            while "\n\n" in buf or "\r\n\r\n" in buf:
                sep = "\n\n" if "\n\n" in buf else "\r\n\r\n"
                block, buf = buf.split(sep, 1)
                data_line = None
                for line in block.splitlines():
                    if line.startswith("data:"):
                        data_line = line[5:].lstrip()
                if not data_line or data_line == "[DONE]":
                    continue
                try:
                    yield json.loads(data_line)
                except json.JSONDecodeError:
                    logger.debug("skip non-json sse data: %s", data_line[:200])


async def stream_job_sse_async(
    *,
    client: Client | AuthenticatedClient,
    job_id: str,
    full_events: bool = False,
) -> AsyncIterator[dict[str, Any]]:
    """Async SSE parser using the client's :class:`httpx.AsyncClient`."""
    hc = client.get_async_httpx_client()
    params = {"full_events": "1"} if full_events else {}
    url = f"/v1/jobs/{job_id}/stream"
    async with hc.stream("GET", url, params=params, headers={"Accept": "text/event-stream"}) as stream:
        stream.raise_for_status()
        buf = ""
        async for raw in stream.aiter_text():
            buf += raw
            while "\n\n" in buf or "\r\n\r\n" in buf:
                sep = "\n\n" if "\n\n" in buf else "\r\n\r\n"
                block, buf = buf.split(sep, 1)
                data_line = None
                for line in block.splitlines():
                    if line.startswith("data:"):
                        data_line = line[5:].lstrip()
                if not data_line or data_line == "[DONE]":
                    continue
                try:
                    yield json.loads(data_line)
                except json.JSONDecodeError:
                    logger.debug("skip non-json sse data: %s", data_line[:200])


def download_artifact_bytes_sync(
    *,
    client: Client | AuthenticatedClient,
    job_id: str,
    kind: str,
    follow_redirects: bool = True,
) -> bytes:
    """``GET /v1/jobs/{id}/artifacts/{kind}`` and return the full body (follows redirects)."""
    hc = client.get_httpx_client()
    url = f"/v1/jobs/{job_id}/artifacts/{kind}"
    r = hc.get(url, follow_redirects=follow_redirects)
    r.raise_for_status()
    return r.content


async def download_artifact_bytes_async(
    *,
    client: Client | AuthenticatedClient,
    job_id: str,
    kind: str,
    follow_redirects: bool = True,
) -> bytes:
    """Async variant of :func:`download_artifact_bytes_sync`."""
    hc = client.get_async_httpx_client()
    url = f"/v1/jobs/{job_id}/artifacts/{kind}"
    r = await hc.get(url, follow_redirects=follow_redirects)
    r.raise_for_status()
    return r.content


def head_artifact_sync(
    *,
    client: Client | AuthenticatedClient,
    job_id: str,
    kind: str,
    follow_redirects: bool = True,
) -> httpx.Response:
    """``HEAD /v1/jobs/{id}/artifacts/{kind}`` (headers only)."""
    hc = client.get_httpx_client()
    url = f"/v1/jobs/{job_id}/artifacts/{kind}"
    return hc.head(url, follow_redirects=follow_redirects)


async def head_artifact_async(
    *,
    client: Client | AuthenticatedClient,
    job_id: str,
    kind: str,
    follow_redirects: bool = True,
) -> httpx.Response:
    hc = client.get_async_httpx_client()
    url = f"/v1/jobs/{job_id}/artifacts/{kind}"
    return await hc.head(url, follow_redirects=follow_redirects)


__all__ = (
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
