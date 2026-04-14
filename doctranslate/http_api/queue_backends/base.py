"""Queue backend protocol (API process enqueues; worker consumes)."""

from __future__ import annotations

from typing import Protocol
from typing import runtime_checkable


@runtime_checkable
class QueueBackend(Protocol):
    """Enqueue work for translation/warmup workers."""

    async def enqueue_translation(self, job_id: str) -> None:
        """Schedule translation for ``job_id`` (metadata row must already exist)."""

    async def enqueue_warmup(self, job_id: str) -> None:
        """Schedule asset warmup for ``job_id``."""

    async def request_cancel(self, job_id: str) -> bool:
        """Best-effort cancel: return True if a cancel signal was applied."""

    def is_healthy(self) -> bool:
        """Return False if the broker is known unreachable (readiness)."""
