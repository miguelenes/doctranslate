"""Job metadata persistence (control plane)."""

from __future__ import annotations

from typing import Any
from typing import Protocol
from typing import runtime_checkable

from doctranslate.schemas.public_api import TranslationErrorPayload
from doctranslate.schemas.public_api import TranslationResult


@runtime_checkable
class JobMetadataStore(Protocol):
    """Persist and load job records (state, progress, errors, results)."""

    def upsert_job(
        self,
        *,
        job_id: str,
        kind: str,
        state: str,
        created_at: Any,
        updated_at: Any,
        progress: dict[str, Any] | None,
        error: TranslationErrorPayload | None,
        result: TranslationResult | None,
        message: str | None,
        retention_expires_at: Any | None,
        request_json: str | None = None,
        cancel_requested_at: Any | None = None,
        worker_heartbeat_at: Any | None = None,
        otel_traceparent: str | None = None,
        progress_seq: int | None = None,
        log_progress_event: bool = False,
        webhook_json: str | None = None,
    ) -> None:
        """Insert or replace the job row.

        When ``log_progress_event`` is true, ``progress`` and ``progress_seq`` must be
        set; an append-only row is written to the job event log for streaming/replay.
        """

    def list_job_events(
        self,
        job_id: str,
        *,
        after_seq: int = 0,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Return ``{seq, event}`` dicts ordered by ``seq`` ascending (for replay APIs)."""

    def enqueue_webhook_delivery(
        self,
        *,
        delivery_id: str,
        job_id: str,
        payload_json: str,
        next_attempt_at_iso: str,
    ) -> bool:
        """Insert a pending delivery row if absent. Returns True when inserted."""

    def claim_webhook_due(
        self,
        *,
        limit: int,
        now_iso: str,
    ) -> list[dict[str, Any]]:
        """Return due rows ``{delivery_id, job_id, payload_json, attempt_count}``."""

    def mark_webhook_attempt(
        self,
        *,
        delivery_id: str,
        attempt_count: int,
        next_attempt_at_iso: str,
        last_http_status: int | None,
        last_error: str | None,
    ) -> None:
        """Update delivery after an attempt."""

    def delete_webhook_delivery(self, delivery_id: str) -> None:
        """Remove a completed delivery row."""

    def get_job_raw(self, job_id: str) -> dict[str, Any] | None:
        """Return a dict compatible with :meth:`JobManager._disk_to_memory`."""

    def delete_job(self, job_id: str) -> None:
        """Remove job metadata."""

    def list_job_ids_expired_before(self, cutoff_iso: str) -> list[str]:
        """List job ids whose ``retention_expires_at`` is set and before ``cutoff_iso`` (UTC ISO)."""
