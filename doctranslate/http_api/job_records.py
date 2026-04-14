"""Normalize persisted job rows into in-memory route records."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from doctranslate.http_api.artifact_store import ArtifactStore
from doctranslate.http_api.metadata_store.sqlite import SqliteJobMetadataStore
from doctranslate.http_api.storage import read_meta
from doctranslate.http_api.storage import utcnow
from doctranslate.schemas.public_api import TranslationErrorPayload
from doctranslate.schemas.public_api import TranslationResult


def parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return utcnow()


def load_job_raw_from_storage(
    *,
    metadata_store: SqliteJobMetadataStore,
    artifact_store: ArtifactStore,
    read_json_meta_fallback: bool,
    job_id: str,
) -> dict[str, Any] | None:
    raw = metadata_store.get_job_raw(job_id)
    if raw is not None:
        return raw
    if read_json_meta_fallback:
        paths = artifact_store.job_paths(job_id)
        return read_meta(paths.meta_path)
    return None


def disk_to_memory_record(
    artifact_store: ArtifactStore,
    job_id: str,
    disk: dict[str, Any],
) -> dict[str, Any]:
    """Build the in-memory job dict shape used by HTTP routes (no ``request`` for disk-only)."""
    paths = artifact_store.job_paths(job_id)
    err = disk.get("error")
    res = disk.get("result")
    return {
        "kind": disk.get("kind", "translation"),
        "state": disk.get("state", "failed"),
        "created_at": parse_dt(disk.get("created_at")),
        "updated_at": parse_dt(disk.get("updated_at")),
        "progress": disk.get("progress"),
        "error": TranslationErrorPayload.model_validate(err) if err else None,
        "result": TranslationResult.model_validate(res) if res else None,
        "paths": paths,
        "request": None,
        "message": disk.get("message"),
    }
