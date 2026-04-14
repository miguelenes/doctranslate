"""Prometheus metrics (optional dependency)."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prometheus_client import Counter
    from prometheus_client import Gauge
    from prometheus_client import Histogram

_METRICS_INITIALIZED = False
_NS = "doctranslate"

_http_requests_total: Counter | None = None
_http_request_duration_seconds: Histogram | None = None
_http_inflight: Gauge | None = None

_jobs_created_total: Counter | None = None
_jobs_terminal_total: Counter | None = None
_job_duration_seconds: Histogram | None = None
_job_queue_depth: Gauge | None = None
_job_enqueue_failures_total: Counter | None = None

_pipeline_stage_duration_seconds: Histogram | None = None
_pipeline_stage_events_total: Counter | None = None
_pipeline_peak_memory_mb: Histogram | None = None

_translator_requests_total: Counter | None = None
_translator_latency_seconds: Histogram | None = None
_translator_tokens_total: Counter | None = None
_translator_estimated_cost_usd_total: Counter | None = None
_translator_concurrent: Gauge | None = None

_assets_warmup_runs_total: Counter | None = None
_assets_warmup_duration_seconds: Histogram | None = None


def init_metrics(namespace: str | None = None) -> bool:
    """Register instruments on first call. Returns False if prometheus_client missing."""
    global _METRICS_INITIALIZED
    global _NS
    if namespace is None:
        try:
            from doctranslate.observability.config import get_observability_settings

            namespace = get_observability_settings().metrics_namespace
        except Exception:
            namespace = "doctranslate"
    global _http_requests_total
    global _http_request_duration_seconds
    global _http_inflight
    global _jobs_created_total
    global _jobs_terminal_total
    global _job_duration_seconds
    global _job_queue_depth
    global _job_enqueue_failures_total
    global _pipeline_stage_duration_seconds
    global _pipeline_stage_events_total
    global _pipeline_peak_memory_mb
    global _translator_requests_total
    global _translator_latency_seconds
    global _translator_tokens_total
    global _translator_estimated_cost_usd_total
    global _translator_concurrent
    global _assets_warmup_runs_total
    global _assets_warmup_duration_seconds

    if _METRICS_INITIALIZED:
        return True

    try:
        from prometheus_client import Counter
        from prometheus_client import Gauge
        from prometheus_client import Histogram
    except ImportError:
        return False

    _NS = namespace
    buckets = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 120.0)

    _http_requests_total = Counter(
        f"{_NS}_http_requests_total",
        "HTTP requests",
        ["method", "route", "status_code"],
    )
    _http_request_duration_seconds = Histogram(
        f"{_NS}_http_request_duration_seconds",
        "HTTP request latency",
        ["method", "route", "status_code"],
        buckets=buckets,
    )
    _http_inflight = Gauge(
        f"{_NS}_http_inflight_requests",
        "In-flight HTTP requests",
        ["route"],
    )

    _jobs_created_total = Counter(
        f"{_NS}_jobs_created_total",
        "Jobs created",
        ["kind", "queue_backend"],
    )
    _jobs_terminal_total = Counter(
        f"{_NS}_jobs_terminal_total",
        "Jobs reached terminal state",
        ["kind", "state", "failure_category"],
    )
    _job_duration_seconds = Histogram(
        f"{_NS}_job_duration_seconds",
        "Job wall-clock duration",
        ["kind", "state"],
        buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1800.0, 3600.0, 7200.0),
    )
    _job_queue_depth = Gauge(
        f"{_NS}_job_queue_depth",
        "Approximate job queue depth by state",
        ["state", "queue_backend"],
    )
    _job_enqueue_failures_total = Counter(
        f"{_NS}_job_enqueue_failures_total",
        "Job enqueue failures",
        ["kind", "reason"],
    )

    _pipeline_stage_duration_seconds = Histogram(
        f"{_NS}_pipeline_stage_duration_seconds",
        "PDF pipeline stage duration",
        ["stage", "kind"],
        buckets=buckets,
    )
    _pipeline_stage_events_total = Counter(
        f"{_NS}_pipeline_stage_events_total",
        "Progress events by type",
        ["stage", "event_type"],
    )
    _pipeline_peak_memory_mb = Histogram(
        f"{_NS}_pipeline_peak_memory_mb",
        "Peak process memory during translate",
        ["kind"],
        buckets=(128, 256, 512, 1024, 2048, 4096, 8192, 16384),
    )

    _translator_requests_total = Counter(
        f"{_NS}_translator_requests_total",
        "Translator routing outcomes",
        ["profile", "provider", "outcome", "failure_category"],
    )
    _translator_latency_seconds = Histogram(
        f"{_NS}_translator_latency_seconds",
        "Translator call latency",
        ["profile", "provider"],
        buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0),
    )
    _translator_tokens_total = Counter(
        f"{_NS}_translator_tokens_total",
        "Token usage",
        ["profile", "provider", "token_type"],
    )
    _translator_estimated_cost_usd_total = Counter(
        f"{_NS}_translator_estimated_cost_usd_total",
        "Estimated LLM cost (USD)",
        ["profile", "provider"],
    )
    _translator_concurrent = Gauge(
        f"{_NS}_translator_concurrent_requests",
        "In-flight translator calls per provider",
        ["profile", "provider"],
    )

    _assets_warmup_runs_total = Counter(
        f"{_NS}_assets_warmup_runs_total",
        "Asset warmup runs",
        ["outcome"],
    )
    _assets_warmup_duration_seconds = Histogram(
        f"{_NS}_assets_warmup_duration_seconds",
        "Asset warmup duration",
        ["outcome"],
        buckets=buckets,
    )

    _METRICS_INITIALIZED = True
    return True


def record_http_request(
    *,
    method: str,
    route: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    if not _METRICS_INITIALIZED or _http_requests_total is None:
        return
    labels = (method, route, str(status_code))
    _http_requests_total.labels(*labels).inc()
    _http_request_duration_seconds.labels(*labels).observe(duration_seconds)


def http_inflight_inc(route: str) -> None:
    if _http_inflight is not None:
        _http_inflight.labels(route).inc()


def http_inflight_dec(route: str) -> None:
    if _http_inflight is not None:
        _http_inflight.labels(route).dec()


def record_job_created(*, kind: str, queue_backend: str) -> None:
    if _jobs_created_total is not None:
        _jobs_created_total.labels(kind, queue_backend).inc()


def record_job_terminal(
    *,
    kind: str,
    state: str,
    failure_category: str = "",
) -> None:
    if _jobs_terminal_total is not None:
        _jobs_terminal_total.labels(kind, state, failure_category or "none").inc()


def record_job_duration(*, kind: str, state: str, seconds: float) -> None:
    if _job_duration_seconds is not None:
        _job_duration_seconds.labels(kind, state).observe(seconds)


def set_job_queue_depth(*, state: str, queue_backend: str, value: int) -> None:
    if _job_queue_depth is not None:
        _job_queue_depth.labels(state, queue_backend).set(value)


def record_job_enqueue_failure(*, kind: str, reason: str) -> None:
    if _job_enqueue_failures_total is not None:
        _job_enqueue_failures_total.labels(kind, reason).inc()


def record_pipeline_stage_duration(
    *,
    stage: str,
    kind: str,
    seconds: float,
) -> None:
    if _pipeline_stage_duration_seconds is not None:
        _pipeline_stage_duration_seconds.labels(stage, kind).observe(seconds)


def record_pipeline_stage_event(*, stage: str, event_type: str) -> None:
    if _pipeline_stage_events_total is not None:
        _pipeline_stage_events_total.labels(stage, event_type).inc()


def record_pipeline_peak_memory_mb(*, kind: str, mb: float) -> None:
    if _pipeline_peak_memory_mb is not None:
        _pipeline_peak_memory_mb.labels(kind).observe(mb)


def record_translator_outcome(
    *,
    profile: str,
    provider: str,
    outcome: str,
    failure_category: str = "",
) -> None:
    if _translator_requests_total is not None:
        _translator_requests_total.labels(
            profile,
            provider,
            outcome,
            failure_category or "none",
        ).inc()


def record_translator_latency(
    *,
    profile: str,
    provider: str,
    seconds: float,
) -> None:
    if _translator_latency_seconds is not None:
        _translator_latency_seconds.labels(profile, provider).observe(seconds)


def record_translator_tokens(
    *,
    profile: str,
    provider: str,
    usage_kind: str,
    amount: int,
) -> None:
    if _translator_tokens_total is not None and amount:
        _translator_tokens_total.labels(profile, provider, usage_kind).inc(amount)


def record_translator_cost(
    *,
    profile: str,
    provider: str,
    usd: float,
) -> None:
    if _translator_estimated_cost_usd_total is not None and usd:
        _translator_estimated_cost_usd_total.labels(profile, provider).inc(usd)


def translator_concurrent_delta(
    *,
    profile: str,
    provider: str,
    delta: int,
) -> None:
    if _translator_concurrent is not None:
        _translator_concurrent.labels(profile, provider).inc(delta)


def record_assets_warmup(*, outcome: str, duration_seconds: float) -> None:
    if _assets_warmup_runs_total is not None:
        _assets_warmup_runs_total.labels(outcome).inc()
    if _assets_warmup_duration_seconds is not None:
        _assets_warmup_duration_seconds.labels(outcome).observe(duration_seconds)


class StageTimer:
    """Context manager for pipeline stage duration."""

    def __init__(self, *, stage: str, kind: str = "translation") -> None:
        self._stage = stage
        self._kind = kind
        self._t0 = 0.0

    def __enter__(self) -> StageTimer:
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        dt = time.perf_counter() - self._t0
        record_pipeline_stage_duration(stage=self._stage, kind=self._kind, seconds=dt)
