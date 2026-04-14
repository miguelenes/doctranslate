"""In-process queue backend (no broker; used implicitly by :class:`~doctranslate.http_api.job_manager.JobManager`)."""

from __future__ import annotations

from doctranslate.http_api.queue_backends.base import QueueBackend


class InProcessQueueBackend:
    """Placeholder type for typing/tests; execution stays in :class:`JobManager`."""

    async def enqueue_translation(self, job_id: str) -> None:  # noqa: ARG002
        raise RuntimeError("InProcessQueueBackend does not enqueue externally")

    async def enqueue_warmup(self, job_id: str) -> None:  # noqa: ARG002
        raise RuntimeError("InProcessQueueBackend does not enqueue externally")

    async def request_cancel(self, job_id: str) -> bool:  # noqa: ARG002
        return False

    def is_healthy(self) -> bool:
        return True


def assert_queue_backend_protocol(_: QueueBackend) -> None:
    """Runtime hook for type checkers (optional)."""
    return None
