"""Pydantic models for HTTP API envelopes (not part of stable ``doctranslate.schemas`` semver)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

from doctranslate.schemas.enums import ArtifactKind
from doctranslate.schemas.public_api import TranslationErrorPayload
from doctranslate.schemas.public_api import TranslationResult
from doctranslate.schemas.versions import PROGRESS_EVENT_VERSION
from doctranslate.schemas.versions import PUBLIC_SCHEMA_VERSION


class ApiErrorEnvelope(BaseModel):
    """Standard JSON error body for HTTP API."""

    model_config = ConfigDict(extra="forbid")

    ok: Literal[False] = False
    schema_version: str = PUBLIC_SCHEMA_VERSION
    request_id: str | None = None
    error: TranslationErrorPayload


class HealthLiveResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"] = "ok"


class HealthReadyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ready: bool
    checks: dict[str, bool] = Field(default_factory=dict)
    message: str | None = None


class RuntimeInfoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app: Literal["doctranslate-http-api"] = "doctranslate-http-api"
    package_version: str
    public_schema_version: str = PUBLIC_SCHEMA_VERSION
    progress_event_version: str = PROGRESS_EVENT_VERSION
    python_version: str
    cache_dir: str


class AssetFileStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    name: str
    present: bool


class AssetStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = PUBLIC_SCHEMA_VERSION
    ready: bool
    files: list[AssetFileStatus] = Field(default_factory=list)


class TranslatorConfigValidateSpec(BaseModel):
    """Optional nested validation for router/local TOML (mirrors CLI intent)."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["router", "local"]
    config_path: str
    routing_profile: str | None = None
    term_extraction_profile: str | None = None
    routing_strategy: str | None = None
    metrics_output: str | None = None
    metrics_json_path: str | None = None
    local_cli: dict[str, Any] | None = None


class ConfigValidateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    translation_request: dict[str, Any] | None = None
    translator_config: TranslatorConfigValidateSpec | None = None

    @model_validator(mode="after")
    def _require_some_payload(self) -> ConfigValidateRequest:
        if self.translation_request is None and self.translator_config is None:
            msg = "Provide translation_request and/or translator_config"
            raise ValueError(msg)
        return self


class ConfigValidateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool = True
    schema_version: str = PUBLIC_SCHEMA_VERSION
    translation_request_valid: bool | None = None
    translator_config_valid: bool | None = None


class InspectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paths: list[str] = Field(min_length=1)


JobState = Literal["queued", "running", "succeeded", "failed", "canceled"]
JobKind = Literal["translation", "warmup"]


class JobCreateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    kind: JobKind
    state: JobState
    status_url: str


class JobStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = PUBLIC_SCHEMA_VERSION
    job_id: str
    kind: JobKind
    state: JobState
    created_at: datetime
    updated_at: datetime
    progress: dict[str, Any] | None = None
    progress_seq: int = 0
    error: TranslationErrorPayload | None = None
    message: str | None = None


class JobEventItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seq: int
    event: dict[str, Any]


class JobEventsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = PUBLIC_SCHEMA_VERSION
    job_id: str
    items: list[JobEventItem] = Field(default_factory=list)


class ArtifactLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: ArtifactKind
    download_url: str
    path: str
    sha256: str | None = None
    size_bytes: int | None = None


class JobResultResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = PUBLIC_SCHEMA_VERSION
    job_id: str
    kind: JobKind
    state: JobState
    translation_result: TranslationResult | None = None
    artifacts: list[ArtifactLink] = Field(default_factory=list)
    error: TranslationErrorPayload | None = None


class JobManifestItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: ArtifactKind
    download_url: str
    path: str
    sha256: str | None = None
    size_bytes: int | None = None
    media_type: str | None = None
    filename: str | None = None
    download_expires_in_seconds: int | None = None


class JobManifestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = PUBLIC_SCHEMA_VERSION
    job_id: str
    kind: JobKind
    state: JobState
    items: list[JobManifestItem] = Field(default_factory=list)
