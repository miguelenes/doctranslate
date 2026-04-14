# OpenAPI artifact

- **Export:** from the repo root, run `uv run python scripts/export_openapi.py`.
- **Output:** [`dist/openapi.json`](dist/openapi.json) — deterministic JSON (`sort_keys=True`, stable indentation).
- **Consumers:** the generated Python HTTP client under [`clients/http-python/`](../clients/http-python/) is regenerated from this file in CI.
