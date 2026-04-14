"""SQLite job metadata store."""

from __future__ import annotations

from pathlib import Path

from doctranslate.http_api.metadata_store.sqlite import SqliteJobMetadataStore
from doctranslate.http_api.storage import utcnow


def test_sqlite_upsert_and_get(tmp_path: Path) -> None:
    db = tmp_path / "m.db"
    store = SqliteJobMetadataStore(db)
    now = utcnow()
    store.upsert_job(
        job_id="j1",
        kind="translation",
        state="queued",
        created_at=now,
        updated_at=now,
        progress=None,
        error=None,
        result=None,
        message=None,
        retention_expires_at=None,
    )
    raw = store.get_job_raw("j1")
    assert raw is not None
    assert raw["job_id"] == "j1"
    assert raw["state"] == "queued"
    store.close()


def test_sqlite_list_expired(tmp_path: Path) -> None:
    db = tmp_path / "m2.db"
    store = SqliteJobMetadataStore(db)
    store.upsert_job(
        job_id="old",
        kind="translation",
        state="succeeded",
        created_at=utcnow(),
        updated_at=utcnow(),
        progress=None,
        error=None,
        result=None,
        message=None,
        retention_expires_at="2020-01-01T00:00:00+00:00",
    )
    ids = store.list_job_ids_expired_before("2030-01-01T00:00:00+00:00")
    assert "old" in ids
    store.close()
