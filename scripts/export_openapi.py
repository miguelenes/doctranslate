#!/usr/bin/env python3
"""Export the FastAPI OpenAPI schema to ``openapi/dist/openapi.json`` (sorted keys)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    data_root = Path(tempfile.mkdtemp(prefix="openapi-export-")) / "api-data"
    # Auth stays disabled for export; OpenAPI still documents security (Bearer + API key)
    # and 401 responses for integrators (see ``apply_openapi_http_api_auth``).
    os.environ.setdefault("DOCTRANSLATE_API_AUTH_MODE", "disabled")
    os.environ["DOCTRANSLATE_API_DATA_ROOT"] = str(data_root)

    from doctranslate.http_api.settings import get_settings

    get_settings.cache_clear()

    from doctranslate.http_api.app import create_app

    app = create_app()
    schema = app.openapi()
    out = repo_root / "openapi" / "dist" / "openapi.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(schema, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(out, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
