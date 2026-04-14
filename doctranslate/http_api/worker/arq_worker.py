"""ARQ worker process for HTTP API translation and warmup jobs."""

from __future__ import annotations

import os

from arq.worker import func

from doctranslate.http_api.redis_settings import redis_settings_from_url


def _redis_url() -> str:
    raw = os.environ.get("DOCTRANSLATE_API_REDIS_URL", "").strip()
    return raw or "redis://127.0.0.1:6379/0"


def _queue_name() -> str:
    raw = os.environ.get("DOCTRANSLATE_API_ARQ_QUEUE_NAME", "").strip()
    return raw or "arq:queue"


async def run_translation_job(_ctx: object, job_id: str) -> None:
    from doctranslate.bootstrap import ensure_user_cache_dirs
    from doctranslate.observability.config import get_observability_settings
    from doctranslate.observability.logging import configure_logging
    from doctranslate.observability.metrics import init_metrics
    from doctranslate.observability.tracing import setup_tracing

    _s = get_observability_settings()
    configure_logging(_s)
    if _s.metrics_enabled:
        init_metrics(_s.metrics_namespace)
    setup_tracing(
        enabled=_s.otel_enabled,
        service_name=_s.otel_service_name,
        resource_attributes=_s.otel_resource_attributes,
    )

    ensure_user_cache_dirs()
    from doctranslate.http_api.settings import get_settings
    from doctranslate.http_api.storage_factory import build_artifact_store
    from doctranslate.http_api.storage_factory import build_metadata_store
    from doctranslate.http_api.worker.runtime import execute_translation_job

    get_settings.cache_clear()
    settings = get_settings()
    metadata_store = build_metadata_store(settings)
    artifact_store = build_artifact_store(settings)
    try:
        await execute_translation_job(
            job_id=job_id,
            metadata_store=metadata_store,
            artifact_store=artifact_store,
            job_timeout_seconds=settings.job_timeout_seconds,
            dual_write_json_meta=settings.dual_write_json_meta,
            artifact_retention_seconds=settings.artifact_retention_seconds,
        )
    finally:
        metadata_store.close()


async def run_warmup_job(_ctx: object, job_id: str) -> None:
    from doctranslate.bootstrap import ensure_user_cache_dirs
    from doctranslate.observability.config import get_observability_settings
    from doctranslate.observability.logging import configure_logging
    from doctranslate.observability.metrics import init_metrics
    from doctranslate.observability.tracing import setup_tracing

    _s = get_observability_settings()
    configure_logging(_s)
    if _s.metrics_enabled:
        init_metrics(_s.metrics_namespace)
    setup_tracing(
        enabled=_s.otel_enabled,
        service_name=_s.otel_service_name,
        resource_attributes=_s.otel_resource_attributes,
    )

    ensure_user_cache_dirs()
    from doctranslate.http_api.settings import get_settings
    from doctranslate.http_api.storage_factory import build_artifact_store
    from doctranslate.http_api.storage_factory import build_metadata_store
    from doctranslate.http_api.worker.runtime import execute_warmup_job

    get_settings.cache_clear()
    settings = get_settings()
    metadata_store = build_metadata_store(settings)
    artifact_store = build_artifact_store(settings)
    try:
        await execute_warmup_job(
            job_id=job_id,
            metadata_store=metadata_store,
            artifact_store=artifact_store,
            dual_write_json_meta=settings.dual_write_json_meta,
            artifact_retention_seconds=settings.artifact_retention_seconds,
        )
    finally:
        metadata_store.close()


class WorkerSettings:
    """ARQ worker configuration (import string: ``doctranslate.http_api.worker.arq_worker.WorkerSettings``)."""

    redis_settings = redis_settings_from_url(_redis_url())
    queue_name = _queue_name()
    allow_abort_jobs = True
    functions = [
        func(run_translation_job, max_tries=1, timeout=float(24 * 3600)),
        func(run_warmup_job, max_tries=1, timeout=3600.0),
    ]
