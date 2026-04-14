"""HTTP middleware: request IDs, Prometheus request metrics."""

from __future__ import annotations

import time
from collections.abc import Callable

from fastapi import Request
from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from doctranslate.observability.config import get_observability_settings
from doctranslate.observability.context import new_request_id
from doctranslate.observability.context import reset_request_id
from doctranslate.observability.context import set_request_id
from doctranslate.observability.metrics import http_inflight_dec
from doctranslate.observability.metrics import http_inflight_inc
from doctranslate.observability.metrics import init_metrics
from doctranslate.observability.metrics import record_http_request


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    if route is not None:
        p = getattr(route, "path", None)
        if isinstance(p, str) and p:
            return p
    return request.url.path.split("?")[0]


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Bind request_id, emit RED-style metrics, optional trace propagation."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_observability_settings()
        hdr = settings.request_id_header
        incoming = request.headers.get(hdr)
        rid = incoming.strip() if incoming else new_request_id()
        tok = set_request_id(rid)
        route = _route_template(request)
        t0 = time.perf_counter()
        metrics_ok = init_metrics(settings.metrics_namespace)
        if metrics_ok:
            http_inflight_inc(route)
        try:
            response = await call_next(request)
        except Exception:
            if metrics_ok:
                http_inflight_dec(route)
                record_http_request(
                    method=request.method,
                    route=route,
                    status_code=500,
                    duration_seconds=time.perf_counter() - t0,
                )
            reset_request_id(tok)
            raise
        if metrics_ok:
            http_inflight_dec(route)
            record_http_request(
                method=request.method,
                route=route,
                status_code=response.status_code,
                duration_seconds=time.perf_counter() - t0,
            )
        reset_request_id(tok)
        response.headers[hdr] = rid
        return response
