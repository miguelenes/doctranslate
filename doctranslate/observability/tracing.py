"""Optional OpenTelemetry tracing."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from contextlib import nullcontext
from typing import Any

logger = logging.getLogger(__name__)

_TRACER_PROVIDER_SET = False


def setup_tracing(
    *,
    enabled: bool,
    service_name: str,
    resource_attributes: str,
) -> bool:
    """Configure OTel SDK if packages are installed and enabled."""
    global _TRACER_PROVIDER_SET
    if not enabled or _TRACER_PROVIDER_SET:
        return _TRACER_PROVIDER_SET

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.debug("OpenTelemetry SDK not installed; tracing disabled")
        return False

    attrs: dict[str, Any] = {"service.name": service_name}
    if resource_attributes.strip():
        for pair in resource_attributes.split(","):
            pair = pair.strip()
            if "=" in pair:
                k, v = pair.split("=", 1)
                attrs[k.strip()] = v.strip()

    resource = Resource.create(attrs)
    provider = TracerProvider(resource=resource)

    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )

        exporter = OTLPSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(exporter))
    except Exception as exc:
        logger.warning(
            "OpenTelemetry OTLP exporter not available (%s); tracing disabled",
            exc,
        )
        return False

    trace.set_tracer_provider(provider)
    _TRACER_PROVIDER_SET = True
    return True


def get_tracer(name: str) -> Any:
    """Return a tracer or a no-op object."""
    try:
        from opentelemetry import trace

        return trace.get_tracer(name)
    except ImportError:
        return _NoOpTracer()


class _NoOpTracer:
    def start_as_current_span(self, *args: Any, **kwargs: Any) -> Any:
        return nullcontext(_NoOpSpan())


class _NoOpSpan:
    def set_attribute(self, *args: Any, **kwargs: Any) -> None:
        return None

    def record_exception(self, *args: Any, **kwargs: Any) -> None:
        return None

    def end(self) -> None:
        return None

    def __enter__(self) -> _NoOpSpan:
        return self

    def __exit__(self, *args: Any) -> None:
        return None


@contextmanager
def span(name: str, **attributes: Any):
    """Start a span if tracing is active."""
    tracer = get_tracer(__name__)
    try:
        with tracer.start_as_current_span(name) as sp:
            if sp is not None:
                for k, v in attributes.items():
                    if v is not None:
                        sp.set_attribute(str(k), v)
            yield sp
    except Exception:
        yield None


def inject_traceparent_carrier() -> dict[str, str]:
    """Build carrier dict with traceparent for propagation."""
    try:
        from opentelemetry import propagate

        carrier: dict[str, str] = {}
        propagate.inject(carrier)
        return carrier
    except ImportError:
        return {}


def traceparent_from_carrier(carrier: dict[str, str]) -> str | None:
    return carrier.get("traceparent")


def attach_context_from_traceparent(traceparent: str | None) -> Any:
    """Return a context token to detach later, or None."""
    if not traceparent:
        return None
    try:
        from opentelemetry import context
        from opentelemetry.propagate import extract

        ctx = extract({"traceparent": traceparent})
        return context.attach(ctx)
    except ImportError:
        return None


def detach_context(token: Any) -> None:
    if token is None:
        return
    try:
        from opentelemetry import context

        context.detach(token)
    except Exception:
        pass
