"""HTTP API runtime settings (environment-driven)."""

from __future__ import annotations

import json
import os
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any
from typing import Literal

from pydantic import AliasChoices
from pydantic import Field
from pydantic import SecretStr
from pydantic import field_validator
from pydantic import model_validator
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
    job_sse_poll_interval_seconds: float = Field(
        default=0.25,
        ge=0.05,
        description="Poll interval for job SSE when not using in-process fan-out (ARQ).",
    )
    public_base_url: str | None = Field(
        default=None,
        description="Optional public origin for webhook/SSE absolute URLs (e.g. https://api.example.com).",
    )
    webhook_https_required: bool = Field(
        default=False,
        description="When true, reject non-https webhook callback URLs at job creation.",
    )
    webhook_allow_hosts: list[str] = Field(
        default_factory=list,
        description="Optional host allowlist for webhooks (CSV env WEBHOOK_ALLOW_HOSTS).",
    )
    webhook_max_attempts: int = Field(default=10, ge=1, le=64)
    webhook_delivery_batch: int = Field(default=5, ge=1, le=50)
    webhook_http_timeout_seconds: float = Field(default=30.0, ge=1.0, le=120.0)
    webhook_sweep_interval_seconds: float = Field(default=2.0, ge=0.5, le=60.0)

    @field_validator("webhook_allow_hosts", mode="before")
    @classmethod
    def _webhook_allow_hosts_csv(cls, v: Any) -> list[str]:
        if v is None or v == "":
            return []
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        return []

    artifact_retention_seconds: float = Field(
        default=86_400.0,
        description="0 disables TTL cleanup.",
    )
    require_assets_ready: bool = Field(default=False)
    warmup_on_startup: Literal["none", "lazy", "eager"] = Field(default="none")

    # --- Authentication (OSS shared secret) ---
    auth_mode: Literal["disabled", "required"] = Field(
        default="disabled",
        description="disabled: no HTTP auth; required: Bearer or API key on protected routes.",
    )
    auth_token: SecretStr | None = Field(
        default=None,
        description="Shared secret when auth_mode=required.",
    )
    auth_header_api_key_name: str = Field(
        default="X-API-Key",
        description="Header name for static API key (in addition to Authorization: Bearer).",
    )
    auth_allow_unauthenticated_probe_paths: bool = Field(
        default=True,
        description="When false, /v1/health/live and /v1/health/ready also require auth.",
    )
    docs_enabled: bool = Field(
        default=True,
        description="Expose /docs, /redoc, and /openapi.json when true.",
    )

    # --- CORS ---
    cors_allow_origins: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed origins (CSV env). Use explicit hosts in production.",
    )
    cors_allow_credentials: bool = Field(default=False)
    cors_allow_methods: list[str] = Field(
        default_factory=lambda: ["*"],
        validation_alias=AliasChoices("CORS_ALLOW_METHODS", "cors_allow_methods"),
    )
    cors_allow_headers: list[str] = Field(
        default_factory=lambda: ["*"],
        validation_alias=AliasChoices("CORS_ALLOW_HEADERS", "cors_allow_headers"),
    )

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

    @field_validator("auth_mode", mode="before")
    @classmethod
    def _normalize_auth_mode(cls, v: object) -> str:
        s = str(v).strip().lower() if v is not None else "disabled"
        if s not in {"disabled", "required"}:
            return "disabled"
        return s

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, v: object) -> list[str]:
        if isinstance(v, list):
            out = [str(x).strip() for x in v if str(x).strip()]
            return out if out else ["*"]
        if isinstance(v, str):
            out = [p.strip() for p in v.split(",") if p.strip()]
            return out if out else ["*"]
        return ["*"]

    @field_validator("cors_allow_methods", "cors_allow_headers", mode="before")
    @classmethod
    def _split_cors_list(cls, v: object) -> list[str]:
        if isinstance(v, list):
            out = [str(x).strip() for x in v if str(x).strip()]
            return out if out else ["*"]
        if isinstance(v, str):
            out = [p.strip() for p in v.split(",") if p.strip()]
            return out if out else ["*"]
        return ["*"]

    @model_validator(mode="after")
    def _validate_auth_token_when_required(self) -> ApiSettings:
        if self.auth_mode == "required":
            if self.auth_token is None:
                msg = "DOCTRANSLATE_API_AUTH_TOKEN must be set when DOCTRANSLATE_API_AUTH_MODE=required"
                raise ValueError(msg)
            if not self.auth_token.get_secret_value().strip():
                msg = "DOCTRANSLATE_API_AUTH_TOKEN must be non-empty when DOCTRANSLATE_API_AUTH_MODE=required"
                raise ValueError(msg)
        return self

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
