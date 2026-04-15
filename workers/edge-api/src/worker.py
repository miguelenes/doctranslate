"""Cloudflare Python Worker entry: Starlette ASGI + DocTranslater schema validation."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Any

import httpx
from forwarding import forward_multipart_to_upstream
from forwarding import validate_translation_request_multipart
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.routing import Route

logger = logging.getLogger(__name__)

try:
    from workers import WorkerEntrypoint
except ImportError:  # pragma: no cover — pytest without workers-py installed

    class WorkerEntrypoint:  # type: ignore[no-redef]
        """Placeholder base class so ``from worker import app`` works in minimal dev envs."""

        env: Any = None


def _upstream_base_url(env: Any) -> str:
    raw = getattr(env, "DOCTRANSLATE_UPSTREAM_URL", None) or getattr(
        env,
        "UPSTREAM_URL",
        None,
    )
    if not raw or not isinstance(raw, str) or not raw.strip():
        return ""
    return raw.rstrip("/")


class _EnvBootstrapMiddleware(BaseHTTPMiddleware):
    """Ensure ``request.scope['env']`` exists for local tests (Workers injects ``env``)."""

    async def dispatch(
        self,
        request: Request,
        call_next: Any,
    ) -> Any:
        if "env" not in request.scope:
            request.scope["env"] = SimpleNamespace(DOCTRANSLATE_UPSTREAM_URL="")
        return await call_next(request)


async def health(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def schema_warmup(_request: Request) -> JSONResponse:
    """Exercise the same imports used for job validation (Pyodide smoke).

    Import ``public_api`` and ``versions`` only — avoid ``import doctranslate.schemas``,
    which loads the package barrel (translator config, etc.).
    """
    import doctranslate.schemas.public_api as public_api  # noqa: PLC0415
    from doctranslate.schemas.public_api import TranslationRequest  # noqa: PLC0415
    from doctranslate.schemas.versions import PUBLIC_SCHEMA_VERSION  # noqa: PLC0415

    _ = PUBLIC_SCHEMA_VERSION
    _ = public_api.__name__
    _ = TranslationRequest.model_json_schema()
    return JSONResponse(
        {
            "ok": True,
            "package": "doctranslate.schemas.public_api",
            "schema_version": PUBLIC_SCHEMA_VERSION,
        },
    )


async def edge_forward_job(request: Request) -> Response:
    """Validate ``translation_request`` then forward multipart to upstream ``POST /v1/jobs``."""
    env = request.scope["env"]
    base = _upstream_base_url(env)
    if not base:
        raise HTTPException(
            status_code=503,
            detail="DOCTRANSLATE_UPSTREAM_URL is not configured",
        )

    form = await request.form()
    tr_json, extra, pdf = await validate_translation_request_multipart(form)
    auth = request.headers.get("authorization")
    upstream = f"{base}/v1/jobs"
    logger.debug("Forwarding validated job to %s", upstream)
    try:
        upstream_resp = await forward_multipart_to_upstream(
            upstream_jobs_url=upstream,
            translation_request_json=tr_json,
            extra_fields=extra,
            input_pdf=pdf,
            authorization=auth,
        )
    except httpx.HTTPError as e:
        logger.warning("Upstream HTTP client error for %s: %s", upstream, e)
        return JSONResponse(
            {"detail": "upstream request failed"},
            status_code=502,
        )
    media_type = upstream_resp.headers.get("content-type", "application/octet-stream")
    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        media_type=media_type,
    )


routes = [
    Route("/health", health, methods=["GET"]),
    Route("/edge/v1/schema-warmup", schema_warmup, methods=["GET"]),
    Route("/edge/v1/jobs", edge_forward_job, methods=["POST"]),
]

app = Starlette(routes=routes)
app.add_middleware(_EnvBootstrapMiddleware)


class Default(WorkerEntrypoint):
    """Cloudflare workerd entry (``main`` in ``wrangler.jsonc``)."""

    async def fetch(self, request: Any) -> Any:
        import asgi  # noqa: PLC0415 — Workers Python ASGI bridge

        return await asgi.fetch(app, request.js_object, self.env)
