"""SQLite-backed job metadata store."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any

from doctranslate.schemas.public_api import TranslationErrorPayload
from doctranslate.schemas.public_api import TranslationResult

logger = logging.getLogger(__name__)


def utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return {str(r[1]) for r in cur.fetchall()}


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
    _migrate_schema(conn)


def _migrate_schema(conn: sqlite3.Connection) -> None:
    cols = _table_columns(conn, "jobs")
    alters: list[str] = []
    if "request_json" not in cols:
        alters.append("ALTER TABLE jobs ADD COLUMN request_json TEXT")
    if "attempt_count" not in cols:
        alters.append(
            "ALTER TABLE jobs ADD COLUMN attempt_count INTEGER NOT NULL DEFAULT 0",
        )
    if "cancel_requested_at" not in cols:
        alters.append("ALTER TABLE jobs ADD COLUMN cancel_requested_at TEXT")
    if "worker_heartbeat_at" not in cols:
        alters.append("ALTER TABLE jobs ADD COLUMN worker_heartbeat_at TEXT")
    if "otel_traceparent" not in cols:
        alters.append("ALTER TABLE jobs ADD COLUMN otel_traceparent TEXT")
    for stmt in alters:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError:
            logger.exception("Schema migration statement failed: %s", stmt)
    conn.commit()


class SqliteJobMetadataStore:
    """SQLite implementation of :class:`~doctranslate.http_api.metadata_store.base.JobMetadataStore`."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._conn = _connect(db_path)
        _init_schema(self._conn)

    def close(self) -> None:
        self._conn.close()

    def count_active_jobs(self) -> int:
        """Count jobs in ``queued`` or ``running`` state."""
        cur = self._conn.execute(
            """
            SELECT COUNT(*) FROM jobs
            WHERE state IN ('queued', 'running')
            """,
        )
        row = cur.fetchone()
        return int(row[0]) if row else 0

    def count_jobs_in_state(self, state: str) -> int:
        cur = self._conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE state = ?",
            (state,),
        )
        row = cur.fetchone()
        return int(row[0]) if row else 0

    def count_jobs_by_state(self) -> dict[str, int]:
        """Return counts keyed by ``state`` for queue depth metrics."""
        cur = self._conn.execute(
            "SELECT state, COUNT(*) AS n FROM jobs GROUP BY state",
        )
        return {str(r[0]): int(r[1]) for r in cur.fetchall()}

    def mark_cancel_requested(
        self,
        job_id: str,
        *,
        iso_timestamp: str,
        message: str | None = "Cancel requested",
    ) -> None:
        """Record that a client requested cancellation (and optional status message)."""
        self._conn.execute(
            """
            UPDATE jobs SET cancel_requested_at = ?, updated_at = ?,
                message = COALESCE(?, message)
            WHERE job_id = ?
            """,
            (iso_timestamp, iso_timestamp, message, job_id),
        )
        self._conn.commit()

    def increment_attempt_count(self, job_id: str) -> int:
        """Increment attempt_count and return the new value."""
        now = utc_iso_now()
        self._conn.execute(
            """
            UPDATE jobs SET attempt_count = attempt_count + 1, updated_at = ?
            WHERE job_id = ?
            """,
            (now, job_id),
        )
        self._conn.commit()
        cur = self._conn.execute(
            "SELECT attempt_count FROM jobs WHERE job_id = ?",
            (job_id,),
        )
        row = cur.fetchone()
        return int(row[0]) if row else 0

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
        creq = None
        if cancel_requested_at is not None:
            creq = (
                cancel_requested_at.isoformat()
                if hasattr(cancel_requested_at, "isoformat")
                else str(cancel_requested_at)
            )
        whb = None
        if worker_heartbeat_at is not None:
            whb = (
                worker_heartbeat_at.isoformat()
                if hasattr(worker_heartbeat_at, "isoformat")
                else str(worker_heartbeat_at)
            )
        self._conn.execute(
            """
            INSERT INTO jobs (
                job_id, kind, state, created_at, updated_at,
                progress_json, error_json, result_json, message, retention_expires_at,
                request_json, cancel_requested_at, worker_heartbeat_at, otel_traceparent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                kind = excluded.kind,
                state = excluded.state,
                created_at = jobs.created_at,
                updated_at = excluded.updated_at,
                progress_json = excluded.progress_json,
                error_json = excluded.error_json,
                result_json = excluded.result_json,
                message = excluded.message,
                retention_expires_at = excluded.retention_expires_at,
                request_json = COALESCE(excluded.request_json, jobs.request_json),
                cancel_requested_at = COALESCE(
                    excluded.cancel_requested_at, jobs.cancel_requested_at
                ),
                worker_heartbeat_at = COALESCE(
                    excluded.worker_heartbeat_at, jobs.worker_heartbeat_at
                ),
                otel_traceparent = COALESCE(
                    jobs.otel_traceparent, excluded.otel_traceparent
                )
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
                request_json,
                creq,
                whb,
                otel_traceparent,
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
        out: dict[str, Any] = {
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
        if d.get("request_json") is not None:
            out["request_json"] = d["request_json"]
        if d.get("cancel_requested_at"):
            out["cancel_requested_at"] = d["cancel_requested_at"]
        if d.get("worker_heartbeat_at"):
            out["worker_heartbeat_at"] = d["worker_heartbeat_at"]
        if d.get("attempt_count") is not None:
            out["attempt_count"] = int(d["attempt_count"])
        if d.get("otel_traceparent"):
            out["otel_traceparent"] = d["otel_traceparent"]
        return out

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
