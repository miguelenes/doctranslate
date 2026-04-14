"""Shared translation / warmup execution for in-process and ARQ workers."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from datetime import datetime
from datetime import timedelta
from typing import Any

from doctranslate.http_api.artifact_store import ArtifactStore
from doctranslate.http_api.metadata_store.sqlite import SqliteJobMetadataStore
from doctranslate.http_api.storage import utcnow
from doctranslate.http_api.storage import write_meta
from doctranslate.schemas.enums import PublicErrorCode
from doctranslate.schemas.public_api import TranslationErrorPayload
from doctranslate.schemas.public_api import TranslationResult

logger = logging.getLogger(__name__)


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
) -> None:
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
            "error": error.model_dump(mode="json") if error else None,
            "result": result.model_dump(mode="json") if result else None,
            "message": message,
        }
        write_meta(paths.meta_path, payload)


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
        return

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


async def execute_warmup_job(
    *,
    job_id: str,
    metadata_store: SqliteJobMetadataStore,
    artifact_store: ArtifactStore,
    dual_write_json_meta: bool,
    artifact_retention_seconds: float,
) -> None:
    """Run asset warmup for ``job_id`` (ARQ worker entry)."""
    raw = metadata_store.get_job_raw(job_id)
    if raw is None:
        return
    if raw.get("state") in {"succeeded", "failed", "canceled"}:
        return
    created_at = datetime.fromisoformat(
        str(raw["created_at"]).replace("Z", "+00:00"),
    )
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
    try:
        from doctranslate.assets import assets as assets_mod

        await asyncio.to_thread(assets_mod.warmup)
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
    except asyncio.CancelledError:
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
        raise
    except Exception as exc:
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
