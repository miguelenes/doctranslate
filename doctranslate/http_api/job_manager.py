"""In-process translation and warmup jobs."""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path
from typing import Any

from doctranslate.http_api.artifact_store import ArtifactStore
from doctranslate.http_api.job_records import disk_to_memory_record
from doctranslate.http_api.job_validation import (
    validate_mounted_input as validate_mounted_path,
)
from doctranslate.http_api.metadata_store.sqlite import SqliteJobMetadataStore
from doctranslate.http_api.storage import JobPaths
from doctranslate.http_api.storage import read_meta
from doctranslate.http_api.storage import utcnow
from doctranslate.http_api.storage import write_meta
from doctranslate.schemas.enums import PublicErrorCode
from doctranslate.schemas.public_api import TranslationErrorPayload
from doctranslate.schemas.public_api import TranslationOptions
from doctranslate.schemas.public_api import TranslationRequest
from doctranslate.schemas.public_api import TranslationResult

logger = logging.getLogger(__name__)


class JobManager:
    """Bounded-concurrency job runner with SQLite metadata (+ optional JSON sidecar)."""

    def __init__(
        self,
        *,
        artifact_store: ArtifactStore,
        metadata_store: SqliteJobMetadataStore,
        max_concurrent: int,
        max_queued: int,
        job_timeout_seconds: float,
        mounted_allow_prefixes: list[str],
        allow_mounted_paths: bool,
        dual_write_json_meta: bool,
        read_json_meta_fallback: bool,
        artifact_retention_seconds: float,
    ) -> None:
        self._artifact_store = artifact_store
        self._metadata_store = metadata_store
        self._sem = asyncio.Semaphore(max(1, max_concurrent))
        self._job_timeout = job_timeout_seconds
        self._mounted_allow_prefixes = mounted_allow_prefixes
        self._allow_mounted_paths = allow_mounted_paths
        self._dual_write_json_meta = dual_write_json_meta
        self._read_json_meta_fallback = read_json_meta_fallback
        self._artifact_retention_seconds = artifact_retention_seconds
        self._jobs: dict[str, dict[str, Any]] = {}
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._lock = asyncio.Lock()
        self._max_active_jobs = max(1, max_queued)

    @property
    def artifact_store(self) -> ArtifactStore:
        return self._artifact_store

    @property
    def store(self) -> ArtifactStore:
        """Backward-compatible alias for the artifact store."""
        return self._artifact_store

    def accepts_new_jobs(self) -> bool:
        """Return False when queued+running jobs reached the configured ceiling."""
        n = sum(1 for r in self._jobs.values() if r["state"] in ("queued", "running"))
        return n < self._max_active_jobs

    def _retention_deadline(self, state: str) -> datetime | None:
        if self._artifact_retention_seconds <= 0:
            return None
        if state not in {"succeeded", "failed", "canceled"}:
            return None
        return utcnow() + timedelta(seconds=self._artifact_retention_seconds)

    def _record_payload(self, job_id: str, rec: dict[str, Any]) -> dict[str, Any]:
        return {
            "job_id": job_id,
            "kind": rec["kind"],
            "state": rec["state"],
            "created_at": rec["created_at"],
            "updated_at": rec["updated_at"],
            "progress": rec.get("progress"),
            "error": rec["error"].model_dump(mode="json") if rec.get("error") else None,
            "result": rec["result"].model_dump(mode="json")
            if rec.get("result")
            else None,
            "message": rec.get("message"),
        }

    def _persist(self, job_id: str) -> None:
        rec = self._jobs.get(job_id)
        if not rec:
            return
        retention = self._retention_deadline(rec["state"])
        self._metadata_store.upsert_job(
            job_id=job_id,
            kind=rec["kind"],
            state=rec["state"],
            created_at=rec["created_at"],
            updated_at=rec["updated_at"],
            progress=rec.get("progress"),
            error=rec.get("error"),
            result=rec.get("result"),
            message=rec.get("message"),
            retention_expires_at=retention,
        )
        if self._dual_write_json_meta:
            paths: JobPaths = rec["paths"]
            write_meta(paths.meta_path, self._record_payload(job_id, rec))

    def load_from_storage(self, job_id: str) -> dict[str, Any] | None:
        raw = self._metadata_store.get_job_raw(job_id)
        if raw is not None:
            return raw
        if self._read_json_meta_fallback:
            paths = self._artifact_store.job_paths(job_id)
            return read_meta(paths.meta_path)
        return None

    async def count_queued(self) -> int:
        async with self._lock:
            return sum(1 for r in self._jobs.values() if r["state"] == "queued")

    async def create_warmup_job(self) -> str:
        async with self._lock:
            n_queued = sum(1 for r in self._jobs.values() if r["state"] == "queued")
            n_running = sum(1 for r in self._jobs.values() if r["state"] == "running")
            if n_queued + n_running >= self._max_active_jobs:
                msg = "Too many queued or active jobs"
                raise RuntimeError(msg)
            job_id = str(uuid.uuid4())
            paths = self._artifact_store.ensure_workspace(job_id)
            now = utcnow()
            self._jobs[job_id] = {
                "kind": "warmup",
                "state": "queued",
                "created_at": now,
                "updated_at": now,
                "progress": None,
                "error": None,
                "result": None,
                "paths": paths,
                "message": None,
            }
            self._persist(job_id)
            task = asyncio.create_task(
                self._run_warmup_wrapped(job_id),
                name=f"warmup-{job_id}",
            )
            self._tasks[job_id] = task
        return job_id

    async def _run_warmup_wrapped(self, job_id: str) -> None:
        try:
            await self._run_warmup(job_id)
        finally:
            self._tasks.pop(job_id, None)

    async def create_translation_job(
        self,
        request: TranslationRequest,
        *,
        input_pdf_path: Path,
        job_id: str | None = None,
    ) -> str:
        async with self._lock:
            n_queued = sum(1 for r in self._jobs.values() if r["state"] == "queued")
            n_running = sum(1 for r in self._jobs.values() if r["state"] == "running")
            if n_queued + n_running >= self._max_active_jobs:
                msg = "Too many queued or active jobs"
                raise RuntimeError(msg)
            jid = job_id or str(uuid.uuid4())
            if jid in self._jobs:
                msg = f"Job id already exists: {jid}"
                raise RuntimeError(msg)
            paths = self._artifact_store.ensure_workspace(jid)
            out_dir = self._artifact_store.local_output_dir(jid)
            base_opts = request.options or TranslationOptions()
            opts_merged = base_opts.model_copy(update={"output_dir": str(out_dir)})
            req = request.model_copy(
                update={
                    "input_pdf": str(input_pdf_path.resolve()),
                    "options": opts_merged,
                },
            )
            now = utcnow()
            self._jobs[jid] = {
                "kind": "translation",
                "state": "queued",
                "created_at": now,
                "updated_at": now,
                "progress": None,
                "error": None,
                "result": None,
                "paths": paths,
                "request": req,
                "message": None,
            }
            self._persist(jid)
            task = asyncio.create_task(
                self._run_translation(jid),
                name=f"translate-{jid}",
            )
            self._tasks[jid] = task
        return jid

    def validate_mounted_input(self, path: Path) -> TranslationErrorPayload | None:
        return validate_mounted_path(
            path,
            allow_mounted_paths=self._allow_mounted_paths,
            mounted_allow_prefixes=self._mounted_allow_prefixes,
        )

    async def cancel(self, job_id: str) -> bool:
        task = self._tasks.get(job_id)
        if task and not task.done():
            task.cancel()
            rec = self._jobs.get(job_id)
            if rec:
                rec["message"] = "Cancel requested"
                rec["updated_at"] = utcnow()
                self._persist(job_id)
            return True
        return False

    async def get_record(self, job_id: str) -> dict[str, Any] | None:
        if job_id in self._jobs:
            return self._jobs[job_id]
        disk = self.load_from_storage(job_id)
        if disk is None:
            return None
        return disk_to_memory_record(self._artifact_store, job_id, disk)

    async def run_ttl_cleanup_once(self) -> None:
        """Delete expired jobs from metadata, sidecars, blobs, and local workspace."""
        cutoff = datetime.now(timezone.utc).isoformat()
        ids = self._metadata_store.list_job_ids_expired_before(cutoff)
        for jid in ids:
            if jid in self._tasks and not self._tasks[jid].done():
                continue
            raw = self._metadata_store.get_job_raw(jid)
            if raw and raw.get("state") == "running":
                continue
            try:
                await self._artifact_store.delete_job_prefix(jid)
            except Exception:
                logger.exception("Artifact cleanup failed for job %s", jid)
            try:
                paths = self._artifact_store.job_paths(jid)
                if paths.meta_path.is_file():
                    paths.meta_path.unlink(missing_ok=True)
            except OSError:
                logger.debug("Could not remove meta.json for %s", jid)
            self._metadata_store.delete_job(jid)

    async def _run_warmup(self, job_id: str) -> None:
        rec = self._jobs[job_id]
        try:
            async with self._sem:
                rec["state"] = "running"
                rec["updated_at"] = utcnow()
                self._persist(job_id)
                from doctranslate.assets import assets as assets_mod

                await asyncio.to_thread(assets_mod.warmup)
                rec["state"] = "succeeded"
                rec["updated_at"] = utcnow()
                rec["message"] = "Warmup completed"
                self._persist(job_id)
        except asyncio.CancelledError:
            rec["state"] = "canceled"
            rec["updated_at"] = utcnow()
            rec["error"] = TranslationErrorPayload(
                code=PublicErrorCode.CANCELED,
                message="Warmup canceled.",
                retryable=False,
            )
            self._persist(job_id)
            raise
        except Exception as exc:
            logger.exception("Warmup job failed")
            rec["state"] = "failed"
            rec["updated_at"] = utcnow()
            rec["error"] = TranslationErrorPayload(
                code=PublicErrorCode.INTERNAL_ERROR,
                message=str(exc),
                retryable=False,
                details={"exception_type": type(exc).__name__},
            )
            self._persist(job_id)

    async def _run_translation(self, job_id: str) -> None:
        rec = self._jobs[job_id]
        req: TranslationRequest = rec["request"]
        try:
            async with self._sem:
                rec["state"] = "running"
                rec["updated_at"] = utcnow()
                self._persist(job_id)
                from doctranslate.api import async_translate

                if self._job_timeout and self._job_timeout > 0:
                    await asyncio.wait_for(
                        self._consume_translate(job_id, async_translate(req)),
                        timeout=self._job_timeout,
                    )
                else:
                    await self._consume_translate(job_id, async_translate(req))
        except asyncio.TimeoutError:
            rec["state"] = "failed"
            rec["updated_at"] = utcnow()
            rec["error"] = TranslationErrorPayload(
                code=PublicErrorCode.INTERNAL_ERROR,
                message="Job exceeded configured timeout.",
                retryable=True,
                details={"timeout_seconds": self._job_timeout},
            )
            self._persist(job_id)
        except asyncio.CancelledError:
            rec["state"] = "canceled"
            rec["updated_at"] = utcnow()
            rec["error"] = TranslationErrorPayload(
                code=PublicErrorCode.CANCELED,
                message="Translation canceled.",
                retryable=False,
            )
            self._persist(job_id)
            raise
        except Exception as exc:
            logger.exception("Translation job failed")
            rec["state"] = "failed"
            rec["updated_at"] = utcnow()
            rec["error"] = TranslationErrorPayload(
                code=PublicErrorCode.INTERNAL_ERROR,
                message=str(exc),
                retryable=False,
                details={"exception_type": type(exc).__name__},
            )
            self._persist(job_id)
        finally:
            self._tasks.pop(job_id, None)

    async def _consume_translate(
        self,
        job_id: str,
        events: AsyncIterator[dict[str, Any]],
    ) -> None:
        rec = self._jobs[job_id]
        async for ev in events:
            rec["progress"] = ev
            rec["updated_at"] = utcnow()
            self._persist(job_id)
            et = ev.get("type")
            if et == "error":
                rec["state"] = "failed"
                err = ev.get("error")
                if isinstance(err, dict):
                    rec["error"] = TranslationErrorPayload.model_validate(err)
                else:
                    rec["error"] = TranslationErrorPayload(
                        code=PublicErrorCode.INTERNAL_ERROR,
                        message=str(err),
                    )
                rec["updated_at"] = utcnow()
                self._persist(job_id)
                return
            if et == "finish":
                tr = ev.get("translation_result")
                if isinstance(tr, dict):
                    rec["result"] = TranslationResult.model_validate(tr)
                elif isinstance(tr, TranslationResult):
                    rec["result"] = tr
                if rec["result"] is not None:
                    rec[
                        "result"
                    ] = await self._artifact_store.finalize_translation_result(
                        job_id,
                        rec["result"],
                    )
                rec["state"] = "succeeded"
                rec["updated_at"] = utcnow()
                self._persist(job_id)
                return
