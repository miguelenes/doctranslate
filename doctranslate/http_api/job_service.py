"""HTTP API job orchestration (in-process vs ARQ queue)."""

from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any
from typing import Literal

from doctranslate.http_api.artifact_store import ArtifactStore
from doctranslate.http_api.job_manager import JobManager
from doctranslate.http_api.job_records import disk_to_memory_record
from doctranslate.http_api.job_records import load_job_raw_from_storage
from doctranslate.http_api.job_validation import validate_mounted_input
from doctranslate.http_api.metadata_store.sqlite import SqliteJobMetadataStore
from doctranslate.http_api.queue_backends.arq_backend import ArqQueueBackend
from doctranslate.http_api.storage import utcnow
from doctranslate.schemas.enums import PublicErrorCode
from doctranslate.schemas.public_api import TranslationErrorPayload
from doctranslate.schemas.public_api import TranslationOptions
from doctranslate.schemas.public_api import TranslationRequest

logger = logging.getLogger(__name__)


class HttpJobService:
    """Facade over :class:`JobManager` (in-process) or ARQ-backed workers."""

    def __init__(
        self,
        *,
        settings: Any,
        artifact_store: ArtifactStore,
        metadata_store: SqliteJobMetadataStore,
        job_manager: JobManager,
        arq_backend: ArqQueueBackend | None,
    ) -> None:
        self._settings = settings
        self._artifact_store = artifact_store
        self._metadata_store = metadata_store
        self._job_manager = job_manager
        self._arq_backend = arq_backend
        self._lock = asyncio.Lock()

    @property
    def artifact_store(self) -> ArtifactStore:
        return self._artifact_store

    @property
    def job_manager(self) -> JobManager:
        """Expose underlying in-process runner (routes may use for edge cases)."""
        return self._job_manager

    @property
    def queue_backend(self) -> Literal["inprocess", "arq"]:
        return self._settings.queue_backend

    def validate_mounted_input(self, path: Path) -> TranslationErrorPayload | None:
        return validate_mounted_input(
            path,
            allow_mounted_paths=self._settings.allow_mounted_paths,
            mounted_allow_prefixes=self._settings.mount_allow_prefixes,
        )

    def accepts_new_jobs(self) -> bool:
        if self._settings.queue_backend == "inprocess":
            return self._job_manager.accepts_new_jobs()
        cap = max(1, self._settings.max_queued_jobs)
        return self._metadata_store.count_active_jobs() < cap

    async def ping_queue(self) -> bool:
        if self._settings.queue_backend != "arq" or self._arq_backend is None:
            return True
        return await self._arq_backend.ping()

    async def count_queued(self) -> int:
        if self._settings.queue_backend == "inprocess":
            return await self._job_manager.count_queued()
        return self._metadata_store.count_jobs_in_state("queued")

    async def create_warmup_job(self) -> str:
        if self._settings.queue_backend == "inprocess":
            return await self._job_manager.create_warmup_job()
        async with self._lock:
            cap = max(1, self._settings.max_queued_jobs)
            if self._metadata_store.count_active_jobs() >= cap:
                msg = "Too many queued or active jobs"
                raise RuntimeError(msg)
            job_id = str(uuid.uuid4())
            self._artifact_store.ensure_workspace(job_id)
            now = utcnow()
            self._metadata_store.upsert_job(
                job_id=job_id,
                kind="warmup",
                state="queued",
                created_at=now,
                updated_at=now,
                progress=None,
                error=None,
                result=None,
                message=None,
                retention_expires_at=None,
            )
            try:
                assert self._arq_backend is not None
                await self._arq_backend.enqueue_warmup(job_id)
            except Exception as exc:
                logger.exception("Warmup enqueue failed")
                self._metadata_store.upsert_job(
                    job_id=job_id,
                    kind="warmup",
                    state="failed",
                    created_at=now,
                    updated_at=utcnow(),
                    progress=None,
                    error=TranslationErrorPayload(
                        code=PublicErrorCode.INTERNAL_ERROR,
                        message=f"Failed to enqueue warmup job: {exc}",
                        retryable=True,
                    ),
                    result=None,
                    message=None,
                    retention_expires_at=None,
                )
                raise
        return job_id

    async def create_translation_job(
        self,
        request: TranslationRequest,
        *,
        input_pdf_path: Path,
        job_id: str | None = None,
    ) -> str:
        if self._settings.queue_backend == "inprocess":
            return await self._job_manager.create_translation_job(
                request,
                input_pdf_path=input_pdf_path,
                job_id=job_id,
            )
        async with self._lock:
            cap = max(1, self._settings.max_queued_jobs)
            if self._metadata_store.count_active_jobs() >= cap:
                msg = "Too many queued or active jobs"
                raise RuntimeError(msg)
            jid = job_id or str(uuid.uuid4())
            if self._metadata_store.get_job_raw(jid) is not None:
                msg = f"Job id already exists: {jid}"
                raise RuntimeError(msg)
            self._artifact_store.ensure_workspace(jid)
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
            req_json = req.model_dump_json()
            self._metadata_store.upsert_job(
                job_id=jid,
                kind="translation",
                state="queued",
                created_at=now,
                updated_at=now,
                progress=None,
                error=None,
                result=None,
                message=None,
                retention_expires_at=None,
                request_json=req_json,
            )
            try:
                assert self._arq_backend is not None
                await self._arq_backend.enqueue_translation(jid)
            except Exception as exc:
                logger.exception("Translation enqueue failed for job %s", jid)
                self._metadata_store.upsert_job(
                    job_id=jid,
                    kind="translation",
                    state="failed",
                    created_at=now,
                    updated_at=utcnow(),
                    progress=None,
                    error=TranslationErrorPayload(
                        code=PublicErrorCode.INTERNAL_ERROR,
                        message=f"Failed to enqueue translation job: {exc}",
                        retryable=True,
                    ),
                    result=None,
                    message=None,
                    retention_expires_at=None,
                    request_json=req_json,
                )
                raise
        return jid

    async def cancel(self, job_id: str) -> bool:
        if self._settings.queue_backend == "inprocess":
            return await self._job_manager.cancel(job_id)
        raw = self._metadata_store.get_job_raw(job_id)
        if raw is None:
            return False
        self._metadata_store.mark_cancel_requested(
            job_id,
            iso_timestamp=utcnow().isoformat(),
            message="Cancel requested",
        )
        aborted = False
        if self._arq_backend is not None:
            aborted = await self._arq_backend.request_cancel(job_id)
        return aborted or raw.get("state") in {"queued", "running"}

    async def get_record(self, job_id: str) -> dict[str, Any] | None:
        if self._settings.queue_backend == "inprocess":
            return await self._job_manager.get_record(job_id)
        disk = load_job_raw_from_storage(
            metadata_store=self._metadata_store,
            artifact_store=self._artifact_store,
            read_json_meta_fallback=self._settings.read_json_meta_fallback,
            job_id=job_id,
        )
        if disk is None:
            return None
        return disk_to_memory_record(self._artifact_store, job_id, disk)

    async def run_ttl_cleanup_once(self) -> None:
        await self._job_manager.run_ttl_cleanup_once()
