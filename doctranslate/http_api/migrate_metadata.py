"""One-off migration: import legacy ``jobs/<id>/meta.json`` into SQLite metadata."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from doctranslate.http_api.metadata_store.sqlite import SqliteJobMetadataStore
from doctranslate.http_api.storage import read_meta
from doctranslate.schemas.public_api import TranslationErrorPayload
from doctranslate.schemas.public_api import TranslationResult

logger = logging.getLogger(__name__)


def migrate_jobs(data_root: Path, db_path: Path | None = None) -> int:
    """Return number of meta.json files imported."""
    root = data_root.expanduser()
    path = db_path or (root / "http_api_metadata.db")
    store = SqliteJobMetadataStore(path)
    jobs_dir = root / "jobs"
    n = 0
    if not jobs_dir.is_dir():
        store.close()
        return 0
    for meta_path in sorted(jobs_dir.glob("*/meta.json")):
        job_id = meta_path.parent.name
        raw = read_meta(meta_path)
        if raw is None:
            continue
        err = raw.get("error")
        res = raw.get("result")
        try:
            store.upsert_job(
                job_id=job_id,
                kind=str(raw.get("kind", "translation")),
                state=str(raw.get("state", "failed")),
                created_at=raw.get("created_at"),
                updated_at=raw.get("updated_at"),
                progress=raw.get("progress"),
                error=TranslationErrorPayload.model_validate(err) if err else None,
                result=TranslationResult.model_validate(res) if res else None,
                message=raw.get("message"),
                retention_expires_at=None,
            )
        except Exception:
            logger.exception("Skipping invalid meta for job %s", job_id)
            continue
        n += 1
    store.close()
    return n


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO)
    p = argparse.ArgumentParser(
        description="Import legacy per-job meta.json files into SQLite metadata DB.",
    )
    p.add_argument(
        "--data-root",
        type=Path,
        required=True,
        help="DOCTRANSLATE_API_DATA_ROOT (directory containing jobs/)",
    )
    p.add_argument(
        "--sqlite-path",
        type=Path,
        default=None,
        help="Target SQLite path (default: <data-root>/http_api_metadata.db)",
    )
    args = p.parse_args(argv)
    n = migrate_jobs(args.data_root, args.sqlite_path)
    logger.info("Imported %d job metadata record(s)", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
