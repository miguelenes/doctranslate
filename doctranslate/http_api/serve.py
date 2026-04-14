"""Run the HTTP API with Uvicorn (``doctranslate serve``)."""

from __future__ import annotations


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
