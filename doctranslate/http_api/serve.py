"""Run the HTTP API with Uvicorn (``doctranslate serve``)."""

from __future__ import annotations


def run_arq_worker(*, burst: bool) -> int:
    """Run the ARQ worker (Redis queue). Requires matching ``DOCTRANSLATE_API_*`` env as the API."""
    from arq.worker import run_worker

    from doctranslate.http_api.worker.arq_worker import WorkerSettings

    run_worker(WorkerSettings, burst=burst)
    return 0


def run_serve(*, host: str, port: int, reload: bool) -> int:
    """Start Uvicorn; blocks until the server stops."""
    import uvicorn

    uvicorn.run(
        "doctranslate.http_api.app:app",
        host=host,
        port=port,
        reload=reload,
        factory=False,
    )
    return 0
