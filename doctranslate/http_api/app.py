"""FastAPI application factory."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from doctranslate.http_api.job_manager import JobManager
from doctranslate.http_api.routes import assets as assets_routes
from doctranslate.http_api.routes import config as config_routes
from doctranslate.http_api.routes import health as health_routes
from doctranslate.http_api.routes import inspect as inspect_routes
from doctranslate.http_api.routes import jobs as jobs_routes
from doctranslate.http_api.settings import get_settings
from doctranslate.http_api.storage import LocalArtifactStore

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    from doctranslate.bootstrap import ensure_user_cache_dirs

    ensure_user_cache_dirs()
    settings = get_settings()
    settings.data_root.mkdir(parents=True, exist_ok=True)
    settings.resolved_tmp_root().mkdir(parents=True, exist_ok=True)
    store = LocalArtifactStore(settings.data_root)
    app.state.job_manager = JobManager(
        store=store,
        max_concurrent=settings.max_concurrent_jobs,
        max_queued=settings.max_queued_jobs,
        job_timeout_seconds=settings.job_timeout_seconds,
        mounted_allow_prefixes=settings.mounted_path_allow_prefixes,
        allow_mounted_paths=settings.allow_mounted_paths,
    )
    if settings.warmup_on_startup == "eager":
        from doctranslate.assets import assets as assets_mod

        logger.info("Running eager asset warmup on startup")
        await asyncio.to_thread(assets_mod.warmup)
    yield


def create_app() -> FastAPI:
    """Build the HTTP API application (ASGI callable)."""
    app = FastAPI(
        title="DocTranslater HTTP API",
        version="1",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(
        _request,
        exc: HTTPException,
    ) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict):
            return JSONResponse(status_code=exc.status_code, content=detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": str(detail)},
        )

    app.include_router(health_routes.router)
    app.include_router(assets_routes.router)
    app.include_router(config_routes.router)
    app.include_router(inspect_routes.router)
    app.include_router(jobs_routes.router)
    return app


# Uvicorn default import target: ``doctranslate.http_api.app:app``
app = create_app()
