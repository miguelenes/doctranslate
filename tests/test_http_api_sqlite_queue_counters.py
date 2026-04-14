"""SQLite metadata helpers for queued job accounting."""

from __future__ import annotations

from pathlib import Path

from doctranslate.http_api.metadata_store.sqlite import SqliteJobMetadataStore
from doctranslate.http_api.storage import utcnow


def test_count_active_and_queued(tmp_path: Path) -> None:
    db = tmp_path / "q.db"
    store = SqliteJobMetadataStore(db)
    now = utcnow()
    for jid, state in (
        ("a", "queued"),
        ("b", "running"),
        ("c", "succeeded"),
    ):
        store.upsert_job(
            job_id=jid,
            kind="translation",
            state=state,
            created_at=now,
            updated_at=now,
            progress=None,
            error=None,
            result=None,
            message=None,
            retention_expires_at=None,
        )
    assert store.count_active_jobs() == 2
    assert store.count_jobs_in_state("queued") == 1
    store.close()


def test_mark_cancel_requested(tmp_path: Path) -> None:
    db = tmp_path / "c.db"
    store = SqliteJobMetadataStore(db)
    now = utcnow()
    store.upsert_job(
        job_id="j1",
        kind="translation",
        state="running",
        created_at=now,
        updated_at=now,
        progress=None,
        error=None,
        result=None,
        message=None,
        retention_expires_at=None,
    )
    store.mark_cancel_requested("j1", iso_timestamp=now.isoformat(), message="Cancel requested")
    raw = store.get_job_raw("j1")
    store.close()
    assert raw is not None
    assert raw.get("cancel_requested_at")
    assert raw.get("message") == "Cancel requested"
