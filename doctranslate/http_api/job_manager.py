"""In-process translation and warmup jobs."""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from typing import Any

from doctranslate.http_api.storage import JobPaths
from doctranslate.http_api.storage import LocalArtifactStore
from doctranslate.http_api.storage import read_meta
from doctranslate.http_api.storage import utcnow
from doctranslate.http_api.storage import write_meta
from doctranslate.schemas.enums import PublicErrorCode
from doctranslate.schemas.public_api import TranslationErrorPayload
from doctranslate.schemas.public_api import TranslationOptions
from doctranslate.schemas.public_api import TranslationRequest
from doctranslate.schemas.public_api import TranslationResult

logger = logging.getLogger(__name__)


def _is_under_allowed_prefix(path: Path, prefixes: list[str]) -> bool:
    try:
        resolved = path.expanduser().resolve()
    except OSError:
        return False
    for raw in prefixes:
        try:
            base = Path(raw).expanduser().resolve()
        except OSError:
            continue
        try:
            resolved.relative_to(base)
            return True
        except ValueError:
            continue
    return False


class JobManager:
    """Bounded-concurrency job runner with JSON sidecar metadata."""

    def __init__(
        self,
        *,
        store: LocalArtifactStore,
        max_concurrent: int,
        max_queued: int,
        job_timeout_seconds: float,
        mounted_allow_prefixes: list[str],
        allow_mounted_paths: bool,
    ) -> None:
        self._store = store
        self._sem = asyncio.Semaphore(max(1, max_concurrent))
        self._job_timeout = job_timeout_seconds
        self._mounted_allow_prefixes = mounted_allow_prefixes
        self._allow_mounted_paths = allow_mounted_paths
        self._jobs: dict[str, dict[str, Any]] = {}
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._lock = asyncio.Lock()
        self._max_active_jobs = max(1, max_queued)

    @property
    def store(self) -> LocalArtifactStore:
        return self._store

    def accepts_new_jobs(self) -> bool:
        """Return False when queued+running jobs reached the configured ceiling."""
        n = sum(1 for r in self._jobs.values() if r["state"] in ("queued", "running"))
        return n < self._max_active_jobs

    def _persist(self, job_id: str) -> None:
        rec = self._jobs.get(job_id)
        if not rec:
            return
        payload = {
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
        paths: JobPaths = rec["paths"]
        write_meta(paths.meta_path, payload)

    def load_from_disk(self, job_id: str) -> dict[str, Any] | None:
        paths = self._store.job_paths(job_id)
        raw = read_meta(paths.meta_path)
        if raw is None:
            return None
        return raw

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
            paths = self._store.job_paths(job_id)
            paths.mkdirs()
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
            paths = self._store.job_paths(jid)
            paths.mkdirs()
            out_dir = paths.output_dir.resolve()
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
        if not self._allow_mounted_paths:
            return TranslationErrorPayload(
                code=PublicErrorCode.UNSUPPORTED_CONFIGURATION,
                message="Mounted path input is disabled by server policy.",
                retryable=False,
            )
        if not path.is_file():
            return TranslationErrorPayload(
                code=PublicErrorCode.NOT_FOUND,
                message=f"Input PDF not found: {path}",
                retryable=False,
            )
        if not _is_under_allowed_prefix(path, self._mounted_allow_prefixes):
            return TranslationErrorPayload(
                code=PublicErrorCode.VALIDATION_ERROR,
                message="Input path is not under an allowed mount prefix.",
                retryable=False,
                details={
                    "path": str(path),
                    "allowed_prefixes": self._mounted_allow_prefixes,
                },
            )
        return None

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
        disk = self.load_from_disk(job_id)
        if disk is None:
            return None
        return self._disk_to_memory(job_id, disk)

    def _disk_to_memory(self, job_id: str, disk: dict[str, Any]) -> dict[str, Any]:
        paths = self._store.job_paths(job_id)
        err = disk.get("error")
        res = disk.get("result")
        return {
            "kind": disk.get("kind", "translation"),
            "state": disk.get("state", "failed"),
            "created_at": _parse_dt(disk.get("created_at")),
            "updated_at": _parse_dt(disk.get("updated_at")),
            "progress": disk.get("progress"),
            "error": TranslationErrorPayload.model_validate(err) if err else None,
            "result": TranslationResult.model_validate(res) if res else None,
            "paths": paths,
            "request": None,
            "message": disk.get("message"),
        }

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
                rec["state"] = "succeeded"
                rec["updated_at"] = utcnow()
                self._persist(job_id)
                return


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return utcnow()
