# HTTP API — Python client (generated)

DocTranslater ships a **generated** Python client under `clients/http-python/` (package `doc_translater_http_api_client`), produced from the committed OpenAPI document ([`openapi/dist/openapi.json`](https://github.com/miguelenes/doctranslate/blob/main/openapi/dist/openapi.json)).

## Regenerating

From the repository root (requires the `dev` dependency group, which includes `openapi-python-client`):

```bash
uv run python scripts/export_openapi.py
uv run python scripts/regenerate_http_client.py
```

The second command runs `openapi-python-client` with [`clients/http-python/openapi-generator.yaml`](https://github.com/miguelenes/doctranslate/blob/main/clients/http-python/openapi-generator.yaml) and a post-step that restores PEP 621 packaging (`scripts/ensure_http_client_packaging.py`).

## Using the client locally

Add the client directory to `PYTHONPATH`, or install the tree in editable mode into your own environment:

```bash
export PYTHONPATH="$(pwd)/clients/http-python${PYTHONPATH:+:$PYTHONPATH}"
```

### Authentication

When `DOCTRANSLATE_API_AUTH_MODE=required`, use `AuthenticatedClient` with `token=...` (Bearer) or configure headers for the API key (see [`http-api.md`](http-api.md#authentication)).

### Typed job creation (`POST /v1/jobs/json`)

The OpenAPI-first route accepts a JSON body (`JobCreateJsonBody`) with a nested `TranslationRequest`, optional `input_pdf_base64`, and optional `webhook`. Multipart `POST /v1/jobs` remains available for shell and Docker examples.

### Helpers (`convenience` module)

The package re-exports small helpers:

- `wait_until_terminal_sync` / `wait_until_terminal_async` — poll `GET /v1/jobs/{id}` until a terminal state.
- `iter_progress_events_sync` / `iter_progress_events_async` — page through `GET /v1/jobs/{id}/events`.
- `stream_job_sse_sync` / `stream_job_sse_async` — parse `GET /v1/jobs/{id}/stream` (`text/event-stream`) into JSON `data` payloads (best-effort framing).
- `download_artifact_bytes_*`, `head_artifact_*` — raw bytes / `HEAD` for artifact URLs.

### Sync example (remote server)

```python
from doc_translater_http_api_client import AuthenticatedClient
from doc_translater_http_api_client import wait_until_terminal_sync
from doc_translater_http_api_client.api.jobs import v1_jobs_create_json
from doc_translater_http_api_client.models.job_create_json_body import JobCreateJsonBody
from doc_translater_http_api_client.models.translation_request import TranslationRequest

client = AuthenticatedClient(base_url="https://api.example.com", token="your-secret")
body = JobCreateJsonBody(
    translation_request=TranslationRequest.from_dict(
        {
            "schema_version": "1",
            "lang_in": "en",
            "lang_out": "zh",
            "input_pdf": "/work/document.pdf",
            "translator": {"mode": "openai", "openai": {"model": "gpt-4o-mini"}},
        }
    ),
)
created = v1_jobs_create_json.sync_detailed(client=client, body=body)
job_id = created.parsed.job_id
final = wait_until_terminal_sync(client=client, job_id=job_id)
```

### Async example

Use `asyncio_detailed` variants from the `api` modules with `client.get_async_httpx_client()` patterns from the generated README, or call `wait_until_terminal_async` from the same `convenience` exports.

### Docker

Point `base_url` at the published service (for example `http://127.0.0.1:8000` when port-mapping the `runtime-api` image). See [`docker.md`](docker.md) for volumes, auth, and queue settings.

## Versioning

- **URL major:** `/v1/...` paths.
- **Public JSON payloads:** `PUBLIC_SCHEMA_VERSION` / `PROGRESS_EVENT_VERSION` from `GET /v1/runtime` align with [`doctranslate.schemas`](public-api-policy.md).
- **Client package:** `doc-translater-http-api-client` uses its own semver in `clients/http-python/pyproject.toml`; bump when the OpenAPI surface changes incompatibly.

## Licensing

The generated client is AGPL-3.0, consistent with the main project.
