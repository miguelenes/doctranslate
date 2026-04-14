"""Shared translation / warmup execution for in-process and ARQ workers."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator
from datetime import datetime
from datetime import timedelta
from typing import Any

from doctranslate.http_api.artifact_store import ArtifactStore
from doctranslate.http_api.metadata_store.sqlite import SqliteJobMetadataStore
from doctranslate.http_api.storage import utcnow
from doctranslate.http_api.storage import write_meta
from doctranslate.http_api.webhook_delivery import maybe_enqueue_terminal_webhook
from doctranslate.schemas.enums import PublicErrorCode
from doctranslate.schemas.public_api import TranslationErrorPayload
from doctranslate.schemas.public_api import TranslationResult

logger = logging.getLogger(__name__)


def _worker_job_wall_seconds(created_at: datetime) -> float:
    return max(0.0, (utcnow() - created_at).total_seconds())


def _emit_worker_job_terminal(
    *,
    kind: str,
    state: str,
    created_at: datetime,
    failure_category: str = "",
) -> None:
    from doctranslate.observability.metrics import record_job_duration
    from doctranslate.observability.metrics import record_job_terminal

    record_job_terminal(
        kind=kind,
        state=state,
        failure_category=failure_category or "none",
    )
    record_job_duration(
        kind=kind,
        state=state,
        seconds=_worker_job_wall_seconds(created_at),
    )


def _retention_deadline(
    state: str,
    artifact_retention_seconds: float,
) -> datetime | None:
    if artifact_retention_seconds <= 0:
        return None
    if state not in {"succeeded", "failed", "canceled"}:
        return None
    return utcnow() + timedelta(seconds=artifact_retention_seconds)


def persist_job_row(
    *,
    metadata_store: SqliteJobMetadataStore,
    artifact_store: ArtifactStore,
    dual_write_json_meta: bool,
    artifact_retention_seconds: float,
    job_id: str,
    kind: str,
    state: str,
    created_at: datetime,
    updated_at: datetime,
    progress: dict[str, Any] | None,
    error: TranslationErrorPayload | None,
    result: TranslationResult | None,
    message: str | None,
    request_json: str | None = None,
    cancel_requested_at: datetime | None = None,
    worker_heartbeat_at: datetime | None = None,
    log_progress_event: bool = False,
) -> None:
    raw = metadata_store.get_job_raw(job_id)
    webhook_json = raw.get("webhook_json") if raw else None
    current_seq = int(raw.get("progress_seq") or 0) if raw else 0
    if log_progress_event and progress is not None:
        use_seq = current_seq + 1
        do_log = True
    else:
        use_seq = current_seq
        do_log = False
    retention = _retention_deadline(state, artifact_retention_seconds)
    metadata_store.upsert_job(
        job_id=job_id,
        kind=kind,
        state=state,
        created_at=created_at,
        updated_at=updated_at,
        progress=progress,
        error=error,
        result=result,
        message=message,
        retention_expires_at=retention,
        request_json=request_json,
        cancel_requested_at=cancel_requested_at,
        worker_heartbeat_at=worker_heartbeat_at,
        progress_seq=use_seq,
        log_progress_event=do_log,
        webhook_json=webhook_json if isinstance(webhook_json, str) else None,
    )
    if dual_write_json_meta:
        paths = artifact_store.job_paths(job_id)
        payload = {
            "job_id": job_id,
            "kind": kind,
            "state": state,
            "created_at": created_at,
            "updated_at": updated_at,
            "progress": progress,
            "progress_seq": use_seq,
            "error": error.model_dump(mode="json") if error else None,
            "result": result.model_dump(mode="json") if result else None,
            "message": message,
        }
        write_meta(paths.meta_path, payload)
    if state in {"succeeded", "failed", "canceled"}:
        maybe_enqueue_terminal_webhook(metadata_store, job_id=job_id)


async def _consume_translate_events(
    *,
    job_id: str,
    events: AsyncIterator[dict[str, Any]],
    metadata_store: SqliteJobMetadataStore,
    artifact_store: ArtifactStore,
    dual_write_json_meta: bool,
    artifact_retention_seconds: float,
    created_at: datetime,
    kind: str,
    cancel_check_every: int,
) -> None:
    n = 0
    async for ev in events:
        n += 1
        if n % cancel_check_every == 0:
            raw = metadata_store.get_job_raw(job_id)
            if raw and raw.get("cancel_requested_at"):
                raise asyncio.CancelledError
        now = utcnow()
        persist_job_row(
            metadata_store=metadata_store,
            artifact_store=artifact_store,
            dual_write_json_meta=dual_write_json_meta,
            artifact_retention_seconds=artifact_retention_seconds,
            job_id=job_id,
            kind=kind,
            state="running",
            created_at=created_at,
            updated_at=now,
            progress=ev,
            error=None,
            result=None,
            message=None,
            log_progress_event=True,
        )
        et = ev.get("type")
        if et == "error":
            err = ev.get("error")
            if isinstance(err, dict):
                err_payload = TranslationErrorPayload.model_validate(err)
            else:
                err_payload = TranslationErrorPayload(
                    code=PublicErrorCode.INTERNAL_ERROR,
                    message=str(err),
                )
            persist_job_row(
                metadata_store=metadata_store,
                artifact_store=artifact_store,
                dual_write_json_meta=dual_write_json_meta,
                artifact_retention_seconds=artifact_retention_seconds,
                job_id=job_id,
                kind=kind,
                state="failed",
                created_at=created_at,
                updated_at=utcnow(),
                progress=ev,
                error=err_payload,
                result=None,
                message=None,
            )
            _emit_worker_job_terminal(
                kind=kind,
                state="failed",
                created_at=created_at,
                failure_category=str(err_payload.code.value),
            )
            return
        if et == "finish":
            tr = ev.get("translation_result")
            if isinstance(tr, dict):
                result = TranslationResult.model_validate(tr)
            elif isinstance(tr, TranslationResult):
                result = tr
            else:
                result = None
            if result is not None:
                result = await artifact_store.finalize_translation_result(
                    job_id,
                    result,
                )
            persist_job_row(
                metadata_store=metadata_store,
                artifact_store=artifact_store,
                dual_write_json_meta=dual_write_json_meta,
                artifact_retention_seconds=artifact_retention_seconds,
                job_id=job_id,
                kind=kind,
                state="succeeded",
                created_at=created_at,
                updated_at=utcnow(),
                progress=ev,
                error=None,
                result=result,
                message=None,
            )
            _emit_worker_job_terminal(
                kind=kind,
                state="succeeded",
                created_at=created_at,
            )
            return


async def execute_translation_job(
    *,
    job_id: str,
    metadata_store: SqliteJobMetadataStore,
    artifact_store: ArtifactStore,
    job_timeout_seconds: float,
    dual_write_json_meta: bool,
    artifact_retention_seconds: float,
) -> None:
    """Run a translation job loaded from SQLite (ARQ worker entry)."""
    from doctranslate.api import async_translate
    from doctranslate.api import validate_request

    raw = metadata_store.get_job_raw(job_id)
    if raw is None:
        logger.warning("execute_translation_job: missing job row %s", job_id)
        return
    if raw.get("state") in {"succeeded", "failed", "canceled"}:
        return
    req_json = raw.get("request_json")
    if not req_json:
        logger.error("execute_translation_job: missing request_json for %s", job_id)
        try:
            ca_bad = datetime.fromisoformat(
                str(raw["created_at"]).replace("Z", "+00:00"),
            )
        except (KeyError, TypeError, ValueError):
            ca_bad = utcnow()
        persist_job_row(
            metadata_store=metadata_store,
            artifact_store=artifact_store,
            dual_write_json_meta=dual_write_json_meta,
            artifact_retention_seconds=artifact_retention_seconds,
            job_id=job_id,
            kind="translation",
            state="failed",
            created_at=ca_bad,
            updated_at=utcnow(),
            progress=None,
            error=TranslationErrorPayload(
                code=PublicErrorCode.INTERNAL_ERROR,
                message="Missing job request payload.",
                retryable=False,
            ),
            result=None,
            message=None,
        )
        _emit_worker_job_terminal(
            kind="translation",
            state="failed",
            created_at=ca_bad,
            failure_category="missing_request",
        )
        return

    metadata_store.increment_attempt_count(job_id)
    created_at = datetime.fromisoformat(
        str(raw["created_at"]).replace("Z", "+00:00"),
    )
    try:
        data = json.loads(req_json)
        req = validate_request(data)
    except Exception as exc:
        logger.exception("Invalid TranslationRequest for job %s", job_id)
        persist_job_row(
            metadata_store=metadata_store,
            artifact_store=artifact_store,
            dual_write_json_meta=dual_write_json_meta,
            artifact_retention_seconds=artifact_retention_seconds,
            job_id=job_id,
            kind="translation",
            state="failed",
            created_at=created_at,
            updated_at=utcnow(),
            progress=None,
            error=TranslationErrorPayload(
                code=PublicErrorCode.VALIDATION_ERROR,
                message=str(exc),
                retryable=False,
            ),
            result=None,
            message=None,
        )
        _emit_worker_job_terminal(
            kind="translation",
            state="failed",
            created_at=created_at,
            failure_category="validation",
        )
        return

    from doctranslate.observability.context import bound_observability_context
    from doctranslate.observability.tracing import attach_context_from_traceparent
    from doctranslate.observability.tracing import detach_context
    from doctranslate.observability.tracing import span

    ctx_tok = attach_context_from_traceparent(raw.get("otel_traceparent"))
    try:
        with bound_observability_context(job_id=job_id, job_kind="translation"):
            with span("job.execute", job_id=job_id, kind="translation"):
                now = utcnow()
                persist_job_row(
                    metadata_store=metadata_store,
                    artifact_store=artifact_store,
                    dual_write_json_meta=dual_write_json_meta,
                    artifact_retention_seconds=artifact_retention_seconds,
                    job_id=job_id,
                    kind="translation",
                    state="running",
                    created_at=created_at,
                    updated_at=now,
                    progress=None,
                    error=None,
                    result=None,
                    message=None,
                    request_json=req_json,
                    worker_heartbeat_at=now,
                )

                try:
                    if job_timeout_seconds and job_timeout_seconds > 0:
                        await asyncio.wait_for(
                            _consume_translate_events(
                                job_id=job_id,
                                events=async_translate(req),
                                metadata_store=metadata_store,
                                artifact_store=artifact_store,
                                dual_write_json_meta=dual_write_json_meta,
                                artifact_retention_seconds=artifact_retention_seconds,
                                created_at=created_at,
                                kind="translation",
                                cancel_check_every=3,
                            ),
                            timeout=job_timeout_seconds,
                        )
                    else:
                        await _consume_translate_events(
                            job_id=job_id,
                            events=async_translate(req),
                            metadata_store=metadata_store,
                            artifact_store=artifact_store,
                            dual_write_json_meta=dual_write_json_meta,
                            artifact_retention_seconds=artifact_retention_seconds,
                            created_at=created_at,
                            kind="translation",
                            cancel_check_every=3,
                        )
                except asyncio.TimeoutError:
                    persist_job_row(
                        metadata_store=metadata_store,
                        artifact_store=artifact_store,
                        dual_write_json_meta=dual_write_json_meta,
                        artifact_retention_seconds=artifact_retention_seconds,
                        job_id=job_id,
                        kind="translation",
                        state="failed",
                        created_at=created_at,
                        updated_at=utcnow(),
                        progress=None,
                        error=TranslationErrorPayload(
                            code=PublicErrorCode.INTERNAL_ERROR,
                            message="Job exceeded configured timeout.",
                            retryable=True,
                            details={"timeout_seconds": job_timeout_seconds},
                        ),
                        result=None,
                        message=None,
                    )
                    _emit_worker_job_terminal(
                        kind="translation",
                        state="failed",
                        created_at=created_at,
                        failure_category="timeout",
                    )
                except asyncio.CancelledError:
                    persist_job_row(
                        metadata_store=metadata_store,
                        artifact_store=artifact_store,
                        dual_write_json_meta=dual_write_json_meta,
                        artifact_retention_seconds=artifact_retention_seconds,
                        job_id=job_id,
                        kind="translation",
                        state="canceled",
                        created_at=created_at,
                        updated_at=utcnow(),
                        progress=None,
                        error=TranslationErrorPayload(
                            code=PublicErrorCode.CANCELED,
                            message="Translation canceled.",
                            retryable=False,
                        ),
                        result=None,
                        message=None,
                    )
                    _emit_worker_job_terminal(
                        kind="translation",
                        state="canceled",
                        created_at=created_at,
                        failure_category="canceled",
                    )
                    raise
                except Exception as exc:
                    logger.exception("Translation job failed (worker)")
                    persist_job_row(
                        metadata_store=metadata_store,
                        artifact_store=artifact_store,
                        dual_write_json_meta=dual_write_json_meta,
                        artifact_retention_seconds=artifact_retention_seconds,
                        job_id=job_id,
                        kind="translation",
                        state="failed",
                        created_at=created_at,
                        updated_at=utcnow(),
                        progress=None,
                        error=TranslationErrorPayload(
                            code=PublicErrorCode.INTERNAL_ERROR,
                            message=str(exc),
                            retryable=False,
                            details={"exception_type": type(exc).__name__},
                        ),
                        result=None,
                        message=None,
                    )
                    _emit_worker_job_terminal(
                        kind="translation",
                        state="failed",
                        created_at=created_at,
                        failure_category=type(exc).__name__,
                    )
    finally:
        detach_context(ctx_tok)


async def execute_warmup_job(
    *,
    job_id: str,
    metadata_store: SqliteJobMetadataStore,
    artifact_store: ArtifactStore,
    dual_write_json_meta: bool,
    artifact_retention_seconds: float,
) -> None:
    """Run asset warmup for ``job_id`` (ARQ worker entry)."""
    from doctranslate.observability.context import bound_observability_context
    from doctranslate.observability.metrics import record_assets_warmup
    from doctranslate.observability.tracing import attach_context_from_traceparent
    from doctranslate.observability.tracing import detach_context
    from doctranslate.observability.tracing import span

    raw = metadata_store.get_job_raw(job_id)
    if raw is None:
        return
    if raw.get("state") in {"succeeded", "failed", "canceled"}:
        return
    created_at = datetime.fromisoformat(
        str(raw["created_at"]).replace("Z", "+00:00"),
    )
    ctx_tok = attach_context_from_traceparent(raw.get("otel_traceparent"))
    try:
        with bound_observability_context(job_id=job_id, job_kind="warmup"):
            with span("job.warmup", job_id=job_id, kind="warmup"):
                now = utcnow()
                persist_job_row(
                    metadata_store=metadata_store,
                    artifact_store=artifact_store,
                    dual_write_json_meta=dual_write_json_meta,
                    artifact_retention_seconds=artifact_retention_seconds,
                    job_id=job_id,
                    kind="warmup",
                    state="running",
                    created_at=created_at,
                    updated_at=now,
                    progress=None,
                    error=None,
                    result=None,
                    message=None,
                )
                t0 = time.perf_counter()
                try:
                    from doctranslate.assets import assets as assets_mod

                    await asyncio.to_thread(assets_mod.warmup)
                    dt = time.perf_counter() - t0
                    record_assets_warmup(outcome="success", duration_seconds=dt)
                    persist_job_row(
                        metadata_store=metadata_store,
                        artifact_store=artifact_store,
                        dual_write_json_meta=dual_write_json_meta,
                        artifact_retention_seconds=artifact_retention_seconds,
                        job_id=job_id,
                        kind="warmup",
                        state="succeeded",
                        created_at=created_at,
                        updated_at=utcnow(),
                        progress=None,
                        error=None,
                        result=None,
                        message="Warmup completed",
                    )
                    _emit_worker_job_terminal(
                        kind="warmup",
                        state="succeeded",
                        created_at=created_at,
                    )
                except asyncio.CancelledError:
                    dt = time.perf_counter() - t0
                    record_assets_warmup(outcome="canceled", duration_seconds=dt)
                    persist_job_row(
                        metadata_store=metadata_store,
                        artifact_store=artifact_store,
                        dual_write_json_meta=dual_write_json_meta,
                        artifact_retention_seconds=artifact_retention_seconds,
                        job_id=job_id,
                        kind="warmup",
                        state="canceled",
                        created_at=created_at,
                        updated_at=utcnow(),
                        progress=None,
                        error=TranslationErrorPayload(
                            code=PublicErrorCode.CANCELED,
                            message="Warmup canceled.",
                            retryable=False,
                        ),
                        result=None,
                        message=None,
                    )
                    _emit_worker_job_terminal(
                        kind="warmup",
                        state="canceled",
                        created_at=created_at,
                        failure_category="canceled",
                    )
                    raise
                except Exception as exc:
                    dt = time.perf_counter() - t0
                    record_assets_warmup(outcome="failed", duration_seconds=dt)
                    logger.exception("Warmup job failed (worker)")
                    persist_job_row(
                        metadata_store=metadata_store,
                        artifact_store=artifact_store,
                        dual_write_json_meta=dual_write_json_meta,
                        artifact_retention_seconds=artifact_retention_seconds,
                        job_id=job_id,
                        kind="warmup",
                        state="failed",
                        created_at=created_at,
                        updated_at=utcnow(),
                        progress=None,
                        error=TranslationErrorPayload(
                            code=PublicErrorCode.INTERNAL_ERROR,
                            message=str(exc),
                            retryable=False,
                            details={"exception_type": type(exc).__name__},
                        ),
                        result=None,
                        message=None,
                    )
                    _emit_worker_job_terminal(
                        kind="warmup",
                        state="failed",
                        created_at=created_at,
                        failure_category=type(exc).__name__,
                    )
    finally:
        detach_context(ctx_tok)
