"""SQLite-backed job metadata store."""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

from doctranslate.schemas.public_api import TranslationErrorPayload
from doctranslate.schemas.public_api import TranslationResult

logger = logging.getLogger(__name__)


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            state TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            progress_json TEXT,
            error_json TEXT,
            result_json TEXT,
            message TEXT,
            retention_expires_at TEXT
        )
        """,
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_jobs_retention
        ON jobs (retention_expires_at)
        """,
    )
    conn.commit()


class SqliteJobMetadataStore:
    """SQLite implementation of :class:`~doctranslate.http_api.metadata_store.base.JobMetadataStore`."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._conn = _connect(db_path)
        _init_schema(self._conn)

    def close(self) -> None:
        self._conn.close()

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
        progress_json = json.dumps(progress) if progress is not None else None
        error_json = error.model_dump_json() if error else None
        result_json = result.model_dump_json() if result else None
        ret = None
        if retention_expires_at is not None:
            ret = (
                retention_expires_at.isoformat()
                if hasattr(retention_expires_at, "isoformat")
                else str(retention_expires_at)
            )
        ca = (
            created_at.isoformat()
            if hasattr(created_at, "isoformat")
            else str(created_at)
        )
        ua = (
            updated_at.isoformat()
            if hasattr(updated_at, "isoformat")
            else str(updated_at)
        )
        self._conn.execute(
            """
            INSERT INTO jobs (
                job_id, kind, state, created_at, updated_at,
                progress_json, error_json, result_json, message, retention_expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                kind = excluded.kind,
                state = excluded.state,
                created_at = jobs.created_at,
                updated_at = excluded.updated_at,
                progress_json = excluded.progress_json,
                error_json = excluded.error_json,
                result_json = excluded.result_json,
                message = excluded.message,
                retention_expires_at = excluded.retention_expires_at
            """,
            (
                job_id,
                kind,
                state,
                ca,
                ua,
                progress_json,
                error_json,
                result_json,
                message,
                ret,
            ),
        )
        self._conn.commit()

    def get_job_raw(self, job_id: str) -> dict[str, Any] | None:
        cur = self._conn.execute(
            "SELECT * FROM jobs WHERE job_id = ?",
            (job_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        d = dict(row)
        progress = d.get("progress_json")
        err = d.get("error_json")
        res = d.get("result_json")
        return {
            "job_id": d["job_id"],
            "kind": d["kind"],
            "state": d["state"],
            "created_at": d["created_at"],
            "updated_at": d["updated_at"],
            "progress": json.loads(progress) if progress else None,
            "error": json.loads(err) if err else None,
            "result": json.loads(res) if res else None,
            "message": d.get("message"),
        }

    def delete_job(self, job_id: str) -> None:
        self._conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
        self._conn.commit()

    def list_job_ids_expired_before(self, cutoff_iso: str) -> list[str]:
        cur = self._conn.execute(
            """
            SELECT job_id FROM jobs
            WHERE retention_expires_at IS NOT NULL
              AND retention_expires_at != ''
              AND retention_expires_at < ?
            """,
            (cutoff_iso,),
        )
        return [str(r[0]) for r in cur.fetchall()]
