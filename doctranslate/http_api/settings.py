"""HTTP API runtime settings (environment-driven)."""

from __future__ import annotations

import os
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator


def _env_bool(key: str, default: bool) -> bool:
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(key: str, default: int) -> int:
    raw = os.environ.get(key)
    if raw is None or not raw.strip():
        return default
    return int(raw)


def _env_float(key: str, default: float) -> float:
    raw = os.environ.get(key)
    if raw is None or not raw.strip():
        return default
    return float(raw)


def _tmp_root_from_env() -> Path | None:
    p = os.environ.get("DOCTRANSLATE_API_TMP_ROOT")
    if not p or not p.strip():
        return None
    return Path(p).expanduser()


class ApiSettings(BaseModel):
    """Settings for :mod:`doctranslate.http_api`."""

    model_config = ConfigDict(extra="forbid")

    data_root: Path = Field(
        default_factory=lambda: Path(
            os.environ.get(
                "DOCTRANSLATE_API_DATA_ROOT",
                str(Path(tempfile.gettempdir()) / "doctranslate-api"),
            ),
        ).expanduser(),
    )
    tmp_root: Path | None = Field(
        default_factory=_tmp_root_from_env,
        description="Optional separate temp root; defaults to data_root/tmp.",
    )
    mounted_path_allow_prefixes: list[str] = Field(
        default_factory=lambda: [
            p.strip()
            for p in os.environ.get(
                "DOCTRANSLATE_API_MOUNT_ALLOW_PREFIXES",
                "/work,/in,/data",
            ).split(",")
            if p.strip()
        ],
    )
    allow_mounted_paths: bool = Field(
        default_factory=lambda: _env_bool("DOCTRANSLATE_API_ALLOW_MOUNTED_PATHS", True),
    )
    max_upload_bytes: int = Field(
        default_factory=lambda: _env_int(
            "DOCTRANSLATE_API_MAX_UPLOAD_BYTES", 256_000_000
        ),
    )
    max_concurrent_jobs: int = Field(
        default_factory=lambda: _env_int("DOCTRANSLATE_API_MAX_CONCURRENT_JOBS", 2),
    )
    max_queued_jobs: int = Field(
        default_factory=lambda: _env_int("DOCTRANSLATE_API_MAX_QUEUED_JOBS", 32),
    )
    job_timeout_seconds: float = Field(
        default_factory=lambda: _env_float("DOCTRANSLATE_API_JOB_TIMEOUT_SECONDS", 0.0),
        description="0 disables per-job timeout.",
    )
    artifact_retention_seconds: float = Field(
        default_factory=lambda: _env_float(
            "DOCTRANSLATE_API_ARTIFACT_RETENTION_SECONDS",
            86_400.0,
        ),
        description="0 disables TTL cleanup.",
    )
    require_assets_ready: bool = Field(
        default_factory=lambda: _env_bool(
            "DOCTRANSLATE_API_REQUIRE_ASSETS_READY", False
        ),
    )
    warmup_on_startup: Literal["none", "lazy", "eager"] = Field(
        default_factory=lambda: (
            os.environ.get(
                "DOCTRANSLATE_API_WARMUP_ON_STARTUP",
                "none",
            )
            .strip()
            .lower()
        ),  # type: ignore[arg-type]
    )

    @model_validator(mode="after")
    def _normalize_warmup(self) -> ApiSettings:
        if self.warmup_on_startup not in {"none", "lazy", "eager"}:
            object.__setattr__(self, "warmup_on_startup", "none")
        return self

    def resolved_tmp_root(self) -> Path:
        if self.tmp_root is not None:
            return self.tmp_root.expanduser()
        return self.data_root / "tmp"


@lru_cache(maxsize=1)
def get_settings() -> ApiSettings:
    """Load settings once per process."""
    return ApiSettings()
