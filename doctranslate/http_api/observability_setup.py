"""Wire observability into the FastAPI app (logging, metrics, tracing, middleware)."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from doctranslate.http_api.observability_middleware import ObservabilityMiddleware
from doctranslate.observability.config import get_observability_settings
from doctranslate.observability.logging import configure_logging
from doctranslate.observability.metrics import init_metrics
from doctranslate.observability.tracing import setup_tracing

logger = logging.getLogger(__name__)


def install_observability(app: FastAPI) -> None:
    """Configure logging/tracing and add middleware + ``/metrics`` mount."""
    settings = get_observability_settings()
    configure_logging(settings)
    if settings.metrics_enabled:
        init_metrics(settings.metrics_namespace)
    ok = setup_tracing(
        enabled=settings.otel_enabled,
        service_name=settings.otel_service_name,
        resource_attributes=settings.otel_resource_attributes,
    )
    if settings.otel_enabled and not ok:
        logger.info("OpenTelemetry tracing requested but SDK/exporter unavailable")

    app.add_middleware(ObservabilityMiddleware)

    if settings.metrics_enabled:
        try:
            from prometheus_client import make_asgi_app

            metrics_app = make_asgi_app()
            path = settings.metrics_path.rstrip("/") or "/metrics"
            if not path.startswith("/"):
                path = "/" + path
            app.mount(path, metrics_app)
        except ImportError:
            logger.warning("prometheus_client missing; cannot mount /metrics")

    if settings.otel_enabled and ok:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            excluded = f"{settings.metrics_path.lstrip('/')},docs,openapi.json,redoc"
            FastAPIInstrumentor.instrument_app(app, excluded_urls=excluded)
        except ImportError:
            logger.debug("opentelemetry-instrumentation-fastapi not installed")
