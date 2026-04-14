#!/usr/bin/env python3
"""Restore packaging files the OpenAPI generator overwrites (PEP 621 + convenience exports)."""

from __future__ import annotations

import sys
from pathlib import Path

_PYPROJECT = """[project]
name = "doc-translater-http-api-client"
version = "0.1.0"
description = "Generated Python client for the DocTranslater HTTP API"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "AGPL-3.0" }
dependencies = [
    "attrs>=22.2.0",
    "httpx>=0.23.0,<0.29.0",
    "python-dateutil>=2.8.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["doc_translater_http_api_client"]

[tool.ruff]
line-length = 120

[tool.ruff.lint]
select = ["F", "I", "UP"]
"""

_INIT = '''"""A client library for accessing DocTranslater HTTP API"""

from .client import AuthenticatedClient, Client
from .convenience import (
    download_artifact_bytes_async,
    download_artifact_bytes_sync,
    head_artifact_async,
    head_artifact_sync,
    iter_progress_events_async,
    iter_progress_events_sync,
    stream_job_sse_async,
    stream_job_sse_sync,
    wait_until_terminal_async,
    wait_until_terminal_sync,
)

__all__ = (
    "AuthenticatedClient",
    "Client",
    "download_artifact_bytes_async",
    "download_artifact_bytes_sync",
    "head_artifact_async",
    "head_artifact_sync",
    "iter_progress_events_async",
    "iter_progress_events_sync",
    "stream_job_sse_async",
    "stream_job_sse_sync",
    "wait_until_terminal_async",
    "wait_until_terminal_sync",
)
'''


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    client_root = root / "clients" / "http-python"
    if not client_root.is_dir():
        print(f"missing client dir: {client_root}", file=sys.stderr)
        return 1
    (client_root / "pyproject.toml").write_text(_PYPROJECT, encoding="utf-8")
    init_path = client_root / "doc_translater_http_api_client" / "__init__.py"
    init_path.write_text(_INIT, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
