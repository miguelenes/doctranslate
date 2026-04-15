# Architecture: Cloudflare and DocTranslater

## Option A (implemented in this folder): Edge Python Worker + upstream API

- **Runtime**: Cloudflare **Python Workers** (Pyodide in a V8 isolate).
- **This service**: Validates `TranslationRequest` using the same Pydantic models as the OSS package (`doctranslate.schemas.public_api` only — **not** `import doctranslate.schemas`, which pulls the heavy package barrel), then **forwards** multipart to a normal DocTranslater **`runtime-api`** deployment.
- **Secrets / config**:
  - **`DOCTRANSLATE_UPSTREAM_URL`**: Base URL of the real API (example: `https://translate.internal`), **without** `/v1/jobs`.
  - Optional alias: **`UPSTREAM_URL`** (same semantics).
  - **Client credentials**: Typically the client sends `Authorization`; the worker forwards it to upstream unchanged. Adjust if you terminate auth at the edge.

**Limits** (Workers platform): keep request bodies small enough for isolate memory; prefer uploading large PDFs to R2 and passing paths if you extend this pattern.

## Option B (not implemented here): Workers + Containers

Run the stock **`runtime-api`** Docker image behind **Workers + Containers** so translation stays in a Linux container while routing stays on Workers. See Cloudflare [Containers](https://developers.cloudflare.com/containers/) and this repo’s [Docker image profiles](../../docs/docker-profiles.md).

Use **Option B** when you need the full stack on Cloudflare without porting to Pyodide. Use **Option A** when you want edge validation and routing in Python while reuse keeps translation on an existing API.

## Pyodide / import audit

Automated tests (`tests/test_schema_and_forwarding.py`) assert that:

- `TranslationRequest` from `doctranslate.schemas.public_api` and `PUBLIC_SCHEMA_VERSION` from `doctranslate.schemas.versions` work with a **base** `DocTranslater` install (path dependency, no `pdf`/`full` extras).

**Manual check** before relying on Pyodide in production:

1. `uv run pywrangler dev` and hit `GET /edge/v1/schema-warmup`.
2. Confirm `POST /edge/v1/jobs` against a test upstream.

**Known constraints**:

- Do **not** install `DocTranslater[full]` into this worker: native wheels (PyMuPDF, ONNXRuntime, OpenCV, etc.) are incompatible with Pyodide.
- Base dependencies include **`regex`** (used by DocTranslater for glossary normalization). If a future Pyodide/workerd build rejects it, replace or vendor that usage in a schemas-only fork or drop the path dependency and copy only the Pydantic models you need.
