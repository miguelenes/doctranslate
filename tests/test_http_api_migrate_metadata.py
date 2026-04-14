"""meta.json → SQLite migration."""

from __future__ import annotations

import json
from pathlib import Path

from doctranslate.http_api.metadata_store.sqlite import SqliteJobMetadataStore
from doctranslate.http_api.migrate_metadata import migrate_jobs


def test_migrate_metadata_imports_meta_json(tmp_path: Path) -> None:
    root = tmp_path / "api-data"
    jid = "11111111-1111-1111-1111-111111111111"
    job_dir = root / "jobs" / jid
    job_dir.mkdir(parents=True)
    payload = {
        "job_id": jid,
        "kind": "translation",
        "state": "succeeded",
        "created_at": "2024-01-01T00:00:00+00:00",
        "updated_at": "2024-01-01T00:01:00+00:00",
        "progress": None,
        "error": None,
        "result": None,
        "message": None,
    }
    (job_dir / "meta.json").write_text(json.dumps(payload), encoding="utf-8")
    n = migrate_jobs(root, root / "meta.db")
    assert n == 1
    store = SqliteJobMetadataStore(root / "meta.db")
    raw = store.get_job_raw(jid)
    store.close()
    assert raw is not None
    assert raw["state"] == "succeeded"
