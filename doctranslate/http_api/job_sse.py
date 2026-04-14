"""Server-Sent Events stream for job progress (replay + live updates)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from fastapi import Request
from fastapi.sse import ServerSentEvent

from doctranslate.http_api.job_progress_hub import JobProgressHub
from doctranslate.http_api.job_service import HttpJobService
from doctranslate.http_api.settings import ApiSettings
from doctranslate.schemas.versions import PUBLIC_SCHEMA_VERSION

_TERMINAL = frozenset({"succeeded", "failed", "canceled"})


def _base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


def _sse_from_progress_row(
    *,
    seq: int,
    ev: dict[str, Any],
    full_events: bool,
    job_id: str,
    base: str,
) -> ServerSentEvent:
    et = str(ev.get("type") or "message")
    if et == "finish" and not full_events:
        data = {
            "type": "job_completed",
            "schema_version": PUBLIC_SCHEMA_VERSION,
            "job_id": job_id,
            "state": "succeeded",
            "seq": seq,
            "result_url": f"{base}/v1/jobs/{job_id}/result",
            "manifest_url": f"{base}/v1/jobs/{job_id}/manifest",
        }
        return ServerSentEvent(data=data, id=str(seq), event="job_completed")
    return ServerSentEvent(data=ev, id=str(seq), event=et)


async def _emit_rows(
    *,
    rows: list[dict[str, Any]],
    full_events: bool,
    job_id: str,
    base: str,
    last_emitted: list[int],
) -> AsyncIterator[ServerSentEvent]:
    for row in rows:
        seq = int(row["seq"])
        ev = row["event"]
        if seq <= last_emitted[0]:
            continue
        if not isinstance(ev, dict):
            continue
        last_emitted[0] = seq
        yield _sse_from_progress_row(
            seq=seq,
            ev=ev,
            full_events=full_events,
            job_id=job_id,
            base=base,
        )


async def job_progress_sse(
    *,
    request: Request,
    job_id: str,
    job_service: HttpJobService,
    settings: ApiSettings,
    hub: JobProgressHub | None,
    full_events: bool,
) -> AsyncIterator[ServerSentEvent]:
    rec = await job_service.get_record(job_id)
    if rec is None:
        yield ServerSentEvent(
            data={"type": "error", "message": "Unknown job"},
            event="error",
        )
        return

    base = _base_url(request)
    last_emitted = [0]
    last_id = request.headers.get("last-event-id")
    if last_id:
        try:
            last_emitted[0] = int(last_id)
        except ValueError:
            last_emitted[0] = 0

    initial_rows = job_service.list_job_events(
        job_id,
        after_seq=last_emitted[0],
        limit=10_000,
    )
    async for ev in _emit_rows(
        rows=initial_rows,
        full_events=full_events,
        job_id=job_id,
        base=base,
        last_emitted=last_emitted,
    ):
        yield ev

    use_hub = (
        settings.queue_backend == "inprocess"
        and hub is not None
        and job_service.job_manager.has_active_runner(job_id)
    )
    poll = max(0.05, float(settings.job_sse_poll_interval_seconds))
    q: asyncio.Queue[Any] | None = None
    if use_hub:
        q = await hub.subscribe(job_id)

    prev_warmup_state: str | None = None
    if rec["kind"] == "warmup":
        prev_warmup_state = str(rec["state"])

    try:
        while True:
            if await request.is_disconnected():
                break
            rec = await job_service.get_record(job_id)
            if rec is None:
                break
            state = str(rec["state"])
            if state in _TERMINAL:
                tail = job_service.list_job_events(
                    job_id,
                    after_seq=last_emitted[0],
                    limit=10_000,
                )
                async for ev in _emit_rows(
                    rows=tail,
                    full_events=full_events,
                    job_id=job_id,
                    base=base,
                    last_emitted=last_emitted,
                ):
                    yield ev
                rec = await job_service.get_record(job_id)
                if rec is None:
                    break
                err = rec.get("error")
                err_d = err.model_dump(mode="json") if err is not None else None
                seq = int(rec.get("progress_seq") or last_emitted[0])
                had_finish = any(
                    isinstance(r.get("event"), dict)
                    and r["event"].get("type") == "finish"
                    for r in tail
                )
                had_engine_error = any(
                    isinstance(r.get("event"), dict)
                    and r["event"].get("type") == "error"
                    for r in tail
                )
                if state == "succeeded" and not full_events and not had_finish:
                    yield ServerSentEvent(
                        data={
                            "type": "job_completed",
                            "schema_version": PUBLIC_SCHEMA_VERSION,
                            "job_id": job_id,
                            "state": "succeeded",
                            "seq": seq,
                            "result_url": f"{base}/v1/jobs/{job_id}/result",
                            "manifest_url": f"{base}/v1/jobs/{job_id}/manifest",
                        },
                        id=str(seq),
                        event="job_completed",
                    )
                elif state in {"failed", "canceled"} and not had_engine_error:
                    yield ServerSentEvent(
                        data={
                            "type": "job_failed",
                            "schema_version": PUBLIC_SCHEMA_VERSION,
                            "job_id": job_id,
                            "state": state,
                            "seq": seq,
                            "error": err_d,
                        },
                        id=str(seq),
                        event="job_failed",
                    )
                break

            if rec["kind"] == "warmup" and state != prev_warmup_state:
                prev_warmup_state = state
                wseq = int(rec.get("progress_seq") or 0)
                yield ServerSentEvent(
                    data={
                        "type": "job_state",
                        "schema_version": PUBLIC_SCHEMA_VERSION,
                        "job_id": job_id,
                        "kind": "warmup",
                        "state": state,
                        "seq": wseq,
                    },
                    id=str(wseq),
                    event="job_state",
                )

            if q is not None:
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=poll)
                except TimeoutError:
                    msg = None
                if msg is not None:
                    seq = int(msg["seq"])
                    ev = msg["event"]
                    if seq > last_emitted[0] and isinstance(ev, dict):
                        last_emitted[0] = seq
                        yield _sse_from_progress_row(
                            seq=seq,
                            ev=ev,
                            full_events=full_events,
                            job_id=job_id,
                            base=base,
                        )
                tail = job_service.list_job_events(
                    job_id,
                    after_seq=last_emitted[0],
                    limit=500,
                )
                async for ev in _emit_rows(
                    rows=tail,
                    full_events=full_events,
                    job_id=job_id,
                    base=base,
                    last_emitted=last_emitted,
                ):
                    yield ev
            else:
                await asyncio.sleep(poll)
                tail = job_service.list_job_events(
                    job_id,
                    after_seq=last_emitted[0],
                    limit=500,
                )
                async for ev in _emit_rows(
                    rows=tail,
                    full_events=full_events,
                    job_id=job_id,
                    base=base,
                    last_emitted=last_emitted,
                ):
                    yield ev
    finally:
        if q is not None and hub is not None:
            await hub.unsubscribe(job_id, q)
