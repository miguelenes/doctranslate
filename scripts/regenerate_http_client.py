#!/usr/bin/env python3
"""Regenerate ``clients/http-python`` from ``openapi/dist/openapi.json``."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    openapi_json = root / "openapi" / "dist" / "openapi.json"
    if not openapi_json.is_file():
        print("Run scripts/export_openapi.py first.", file=sys.stderr)
        return 1
    cfg = root / "clients" / "http-python" / "openapi-generator.yaml"
    cmd = [
        sys.executable,
        "-m",
        "openapi_python_client",
        "generate",
        "--path",
        str(openapi_json),
        "--output-path",
        str(root / "clients" / "http-python"),
        "--overwrite",
        "--config",
        str(cfg),
    ]
    return int(subprocess.call(cmd, cwd=str(root)))


if __name__ == "__main__":
    raise SystemExit(main())
