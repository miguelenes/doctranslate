"""FastAPI application factory."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from arq.connections import create_pool
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from doctranslate.http_api.auth import OperatorPathsAuthMiddleware
from doctranslate.http_api.auth import install_openapi_auth_extension
from doctranslate.http_api.job_manager import JobManager
from doctranslate.http_api.job_progress_hub import JobProgressHub
from doctranslate.http_api.job_service import HttpJobService
from doctranslate.http_api.observability_setup import install_observability
from doctranslate.http_api.queue_backends.arq_backend import ArqQueueBackend
from doctranslate.http_api.redis_settings import redis_settings_from_url
from doctranslate.http_api.routes import assets as assets_routes
from doctranslate.http_api.routes import config as config_routes
from doctranslate.http_api.routes import health as health_routes
from doctranslate.http_api.routes import inspect as inspect_routes
from doctranslate.http_api.routes import jobs as jobs_routes
from doctranslate.http_api.settings import get_settings
from doctranslate.http_api.storage_factory import build_artifact_store
from doctranslate.http_api.storage_factory import build_metadata_store

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    from doctranslate.bootstrap import ensure_user_cache_dirs

    ensure_user_cache_dirs()
    settings = get_settings()
    settings.data_root.mkdir(parents=True, exist_ok=True)
    settings.resolved_tmp_root().mkdir(parents=True, exist_ok=True)
    artifact_store = build_artifact_store(settings)
    metadata_store = build_metadata_store(settings)
    app.state.artifact_store = artifact_store
    app.state.metadata_store = metadata_store
    arq_pool = None
    arq_backend = None
    if settings.queue_backend == "arq":
        redis_settings = redis_settings_from_url(settings.redis_url)
        arq_pool = await create_pool(redis_settings)
        arq_backend = ArqQueueBackend(
            arq_pool,
            queue_name=settings.arq_queue_name,
        )
        await arq_backend.ping()
    app.state.arq_pool = arq_pool
    progress_hub = JobProgressHub()
    app.state.job_progress_hub = progress_hub
    job_manager = JobManager(
        artifact_store=artifact_store,
        metadata_store=metadata_store,
        max_concurrent=settings.max_concurrent_jobs,
        max_queued=settings.max_queued_jobs,
        job_timeout_seconds=settings.job_timeout_seconds,
        mounted_allow_prefixes=settings.mount_allow_prefixes,
        allow_mounted_paths=settings.allow_mounted_paths,
        dual_write_json_meta=settings.dual_write_json_meta,
        read_json_meta_fallback=settings.read_json_meta_fallback,
        artifact_retention_seconds=settings.artifact_retention_seconds,
        progress_hub=progress_hub,
    )
    app.state.job_manager = job_manager
    app.state.job_service = HttpJobService(
        settings=settings,
        artifact_store=artifact_store,
        metadata_store=metadata_store,
        job_manager=job_manager,
        arq_backend=arq_backend,
    )
    stop_ttl = asyncio.Event()

    async def _ttl_sweep() -> None:
        while not stop_ttl.is_set():
            try:
                await asyncio.wait_for(
                    stop_ttl.wait(),
                    timeout=settings.ttl_cleanup_interval_seconds,
                )
                break
            except asyncio.TimeoutError:
                try:
                    await app.state.job_service.run_ttl_cleanup_once()
                except Exception:
                    logger.exception("TTL cleanup sweep failed")

    ttl_task = asyncio.create_task(_ttl_sweep(), name="http-api-ttl")
    stop_wh = asyncio.Event()

    async def _webhook_sweep() -> None:
        from doctranslate.http_api.webhook_delivery import run_webhook_delivery_sweep

        while not stop_wh.is_set():
            try:
                await asyncio.wait_for(
                    stop_wh.wait(),
                    timeout=settings.webhook_sweep_interval_seconds,
                )
                break
            except asyncio.TimeoutError:
                try:
                    await run_webhook_delivery_sweep(
                        metadata_store=metadata_store,
                        settings=settings,
                    )
                except Exception:
                    logger.exception("Webhook delivery sweep failed")

    wh_task = asyncio.create_task(_webhook_sweep(), name="http-api-webhooks")
    if settings.warmup_on_startup == "eager":
        from doctranslate.assets import assets as assets_mod

        logger.info("Running eager asset warmup on startup")
        await asyncio.to_thread(assets_mod.warmup)
    try:
        yield
    finally:
        stop_ttl.set()
        ttl_task.cancel()
        try:
            await ttl_task
        except asyncio.CancelledError:
            pass
        stop_wh.set()
        wh_task.cancel()
        try:
            await wh_task
        except asyncio.CancelledError:
            pass
        metadata_store.close()
        if arq_pool is not None:
            await arq_pool.close(close_connection_pool=True)


def create_app() -> FastAPI:
    """Build the HTTP API application (ASGI callable)."""
    settings = get_settings()
    docs_kwargs: dict = {}
    if not settings.docs_enabled:
        docs_kwargs = {
            "docs_url": None,
            "redoc_url": None,
            "openapi_url": None,
        }
    app = FastAPI(
        title="DocTranslater HTTP API",
        version="1",
        lifespan=lifespan,
        **docs_kwargs,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
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
    install_observability(app)
    app.add_middleware(OperatorPathsAuthMiddleware)
    install_openapi_auth_extension(app)
    return app


# Uvicorn default import target: ``doctranslate.http_api.app:app``
app = create_app()
