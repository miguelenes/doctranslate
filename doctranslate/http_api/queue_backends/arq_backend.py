"""ARQ (Redis) queue backend for HTTP API jobs."""

from __future__ import annotations

import logging

from arq.connections import ArqRedis
from arq.jobs import Job

logger = logging.getLogger(__name__)


class ArqQueueBackend:
    """Enqueue DocTranslater HTTP API jobs to ARQ workers."""

    def __init__(self, pool: ArqRedis, *, queue_name: str) -> None:
        self._pool = pool
        self._queue_name = queue_name
        self._last_ping_ok = True

    async def ping(self) -> bool:
        """Return True if Redis is reachable."""
        try:
            await self._pool.ping()
        except Exception:
            logger.exception("ARQ Redis ping failed")
            self._last_ping_ok = False
            return False
        self._last_ping_ok = True
        return True

    async def enqueue_translation(self, job_id: str) -> None:
        await self._pool.enqueue_job(
            "run_translation_job",
            job_id,
            _job_id=job_id,
            _queue_name=self._queue_name,
        )

    async def enqueue_warmup(self, job_id: str) -> None:
        await self._pool.enqueue_job(
            "run_warmup_job",
            job_id,
            _job_id=job_id,
            _queue_name=self._queue_name,
        )

    async def request_cancel(self, job_id: str) -> bool:
        """Signal ARQ to abort the job (best-effort)."""
        job = Job(job_id, self._pool, _queue_name=self._queue_name)
        try:
            return await job.abort(timeout=5.0)
        except Exception:
            logger.debug("ARQ abort for job %s did not complete cleanly", job_id)
            return False

    def is_healthy(self) -> bool:
        return self._last_ping_ok
