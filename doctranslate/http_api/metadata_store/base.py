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
    ) -> None:
        """Insert or replace the job row."""

    def get_job_raw(self, job_id: str) -> dict[str, Any] | None:
        """Return a dict compatible with :meth:`JobManager._disk_to_memory`."""

    def delete_job(self, job_id: str) -> None:
        """Remove job metadata."""

    def list_job_ids_expired_before(self, cutoff_iso: str) -> list[str]:
        """List job ids whose ``retention_expires_at`` is set and before ``cutoff_iso`` (UTC ISO)."""
