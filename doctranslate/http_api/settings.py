"""HTTP API runtime settings (environment-driven)."""

from __future__ import annotations

import json
import os
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices
from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


def _default_mount_prefixes() -> list[str]:
    return [
        p.strip()
        for p in os.environ.get(
            "DOCTRANSLATE_API_MOUNT_ALLOW_PREFIXES",
            "/work,/in,/data",
        ).split(",")
        if p.strip()
    ]


class ApiSettings(BaseSettings):
    """Settings for :mod:`doctranslate.http_api`."""

    model_config = SettingsConfigDict(
        env_prefix="DOCTRANSLATE_API_",
        extra="ignore",
    )

    data_root: Path = Field(
        default_factory=lambda: Path(tempfile.gettempdir()) / "doctranslate-api",
    )
    tmp_root: Path | None = Field(
        default=None,
        description="Optional separate temp root; defaults to data_root/tmp.",
        validation_alias=AliasChoices("TMP_ROOT", "tmp_root"),
    )
    mount_allow_prefixes: list[str] = Field(
        default_factory=_default_mount_prefixes,
        validation_alias=AliasChoices(
            "MOUNT_ALLOW_PREFIXES",
            "mount_allow_prefixes",
            "mounted_path_allow_prefixes",
        ),
    )
    allow_mounted_paths: bool = True
    max_upload_bytes: int = Field(default=256_000_000)
    max_concurrent_jobs: int = Field(default=2)
    max_queued_jobs: int = Field(default=32)
    job_timeout_seconds: float = Field(
        default=0.0, description="0 disables per-job timeout."
    )
    artifact_retention_seconds: float = Field(
        default=86_400.0,
        description="0 disables TTL cleanup.",
    )
    require_assets_ready: bool = Field(default=False)
    warmup_on_startup: Literal["none", "lazy", "eager"] = Field(default="none")

    # --- Pluggable storage / metadata ---
    artifact_storage: Literal["local", "remote"] = Field(
        default="local",
        description="local: disk only; remote: mirror uploads/outputs to fsspec URL.",
    )
    artifact_remote_root: str = Field(
        default="",
        description="fsspec URL root (e.g. s3://bucket/prefix or file:///tmp/remote).",
    )
    fsspec_storage_options_json: str = Field(
        default="",
        description="JSON object passed as storage_options to fsspec (e.g. S3 keys).",
    )
    metadata_sqlite_path: Path | None = Field(
        default=None,
        description="SQLite DB path; default data_root/http_api_metadata.db",
    )
    dual_write_json_meta: bool = Field(
        default=True,
        description="Also write legacy jobs/<id>/meta.json when true.",
    )
    read_json_meta_fallback: bool = Field(
        default=True,
        description="If SQLite misses a row, try reading legacy meta.json.",
    )
    artifact_download_mode: Literal["proxy", "redirect"] = Field(
        default="proxy",
        description="redirect: use presigned URLs in /result when possible.",
    )
    presign_expires_seconds: int = Field(default=3600, ge=60, le=604_800)
    ttl_cleanup_interval_seconds: float = Field(
        default=300.0,
        ge=30.0,
        description="Background TTL sweep interval in seconds.",
    )

    # --- Queue / worker execution ---
    queue_backend: Literal["inprocess", "arq"] = Field(
        default="inprocess",
        description="inprocess: asyncio tasks in API; arq: Redis-backed workers.",
    )
    redis_url: str = Field(
        default="redis://127.0.0.1:6379/0",
        description="Redis URL for ARQ (when queue_backend=arq).",
    )
    arq_queue_name: str = Field(
        default="arq:queue",
        description="ARQ queue name; must match the worker process.",
    )

    @field_validator("mount_allow_prefixes", mode="before")
    @classmethod
    def _split_mount_prefixes(cls, v: object) -> list[str]:
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        return _default_mount_prefixes()

    @field_validator("queue_backend", mode="before")
    @classmethod
    def _normalize_queue_backend(cls, v: object) -> str:
        s = str(v).strip().lower() if v is not None else "inprocess"
        if s not in {"inprocess", "arq"}:
            return "inprocess"
        return s

    @field_validator("warmup_on_startup", mode="before")
    @classmethod
    def _normalize_warmup(cls, v: object) -> str:
        s = str(v).strip().lower() if v is not None else "none"
        if s not in {"none", "lazy", "eager"}:
            return "none"
        return s

    @field_validator("metadata_sqlite_path", mode="before")
    @classmethod
    def _coerce_metadata_path(cls, v: object) -> Path | None:
        if v is None or v == "":
            return None
        return Path(str(v)).expanduser()

    def resolved_tmp_root(self) -> Path:
        if self.tmp_root is not None:
            return self.tmp_root.expanduser()
        return self.data_root / "tmp"

    @property
    def mounted_path_allow_prefixes(self) -> list[str]:
        """Alias for compatibility with older field name."""
        return self.mount_allow_prefixes

    def parsed_fsspec_storage_options(self) -> dict:
        raw = (self.fsspec_storage_options_json or "").strip()
        if not raw:
            return {}
        try:
            out = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return out if isinstance(out, dict) else {}


@lru_cache(maxsize=1)
def get_settings() -> ApiSettings:
    """Load settings once per process."""
    return ApiSettings()
