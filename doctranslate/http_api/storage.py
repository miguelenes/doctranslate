"""Filesystem layout for API jobs and artifacts."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class JobPaths:
    """Resolved paths for one job workspace."""

    job_id: str
    root: Path
    input_dir: Path
    work_dir: Path
    output_dir: Path
    meta_path: Path

    @classmethod
    def under(cls, data_root: Path, job_id: str) -> JobPaths:
        root = data_root / "jobs" / job_id
        return cls(
            job_id=job_id,
            root=root,
            input_dir=root / "input",
            work_dir=root / "work",
            output_dir=root / "output",
            meta_path=root / "meta.json",
        )

    def mkdirs(self) -> None:
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


def write_meta(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    data = json.dumps(payload, default=_json_default, indent=2)
    tmp.write_text(data, encoding="utf-8")
    tmp.replace(path)


def read_meta(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _json_default(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if isinstance(obj, Path):
        return str(obj)
    msg = f"Unsupported JSON type: {type(obj)}"
    raise TypeError(msg)


class LocalArtifactStore:
    """Maps job output directory to downloadable artifacts."""

    def __init__(self, data_root: Path) -> None:
        self.data_root = data_root

    def job_paths(self, job_id: str) -> JobPaths:
        return JobPaths.under(self.data_root, job_id)
