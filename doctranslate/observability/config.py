"""Environment-driven observability settings (shared by CLI, HTTP API, workers)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache


class ObservabilityProfile(str, Enum):
    """High-level preset combining logs, metrics, and traces."""

    MINIMAL = "minimal"  # JSON logs + Prometheus (default OSS)
    LOGS_ONLY = "logs_only"
    PROMETHEUS = "prometheus"  # explicit richer histograms (same as minimal for now)
    OTLP = "otlp"  # logs + OTLP traces (metrics still Prometheus unless extended)


@dataclass(frozen=True)
class ObservabilitySettings:
    """Resolved observability configuration."""

    profile: ObservabilityProfile
    log_format: str  # json | console
    log_level: str
    redact_user_text: bool
    request_id_header: str
    metrics_enabled: bool
    metrics_path: str
    metrics_namespace: str
    otel_enabled: bool
    otel_service_name: str
    otel_resource_attributes: str


def _env_bool(key: str, default: bool) -> bool:
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_str(key: str, default: str) -> str:
    raw = os.environ.get(key)
    return raw.strip() if raw and raw.strip() else default


@lru_cache(maxsize=1)
def get_observability_settings() -> ObservabilitySettings:
    """Load once per process from ``DOCTRANSLATE_*`` environment variables."""
    prof_raw = _env_str("DOCTRANSLATE_OBS_PROFILE", ObservabilityProfile.MINIMAL.value).lower()
    try:
        profile = ObservabilityProfile(prof_raw)
    except ValueError:
        profile = ObservabilityProfile.MINIMAL

    log_format = _env_str("DOCTRANSLATE_LOG_FORMAT", "json").lower()
    if log_format not in {"json", "console"}:
        log_format = "json"

    log_level = _env_str("DOCTRANSLATE_LOG_LEVEL", "INFO").upper()

    metrics_enabled = _env_bool("DOCTRANSLATE_METRICS_ENABLED", True)
    if profile == ObservabilityProfile.LOGS_ONLY:
        metrics_enabled = False

    otel_enabled = _env_bool("DOCTRANSLATE_OTEL_ENABLED", False)
    if profile == ObservabilityProfile.OTLP:
        otel_enabled = True

    return ObservabilitySettings(
        profile=profile,
        log_format=log_format,
        log_level=log_level,
        redact_user_text=_env_bool("DOCTRANSLATE_LOG_REDACT_USER_TEXT", True),
        request_id_header=_env_str("DOCTRANSLATE_REQUEST_ID_HEADER", "X-Request-ID"),
        metrics_enabled=metrics_enabled,
        metrics_path=_env_str("DOCTRANSLATE_METRICS_PATH", "/metrics"),
        metrics_namespace=_env_str("DOCTRANSLATE_METRICS_NAMESPACE", "doctranslate"),
        otel_enabled=otel_enabled,
        otel_service_name=_env_str("DOCTRANSLATE_OTEL_SERVICE_NAME", "doctranslate"),
        otel_resource_attributes=_env_str("DOCTRANSLATE_OTEL_RESOURCE_ATTRIBUTES", ""),
    )


def reset_observability_settings_cache() -> None:
    """Clear settings cache (tests)."""
    get_observability_settings.cache_clear()
