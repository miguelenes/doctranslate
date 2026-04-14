# HTTP API (container service)

DocTranslater ships an **optional** HTTP API for running the engine inside a container and driving it from other systems. It wraps the stable Python surface (`doctranslate.api`, `doctranslate.schemas`) and does **not** shell out to the CLI.

## Install

```bash
pip install "DocTranslater[full,api]"
# or minimal API stack on top of an existing PDF install:
pip install "DocTranslater[pdf,cli,llm,tm,vision,api]"
```

Development lockfile (this repo):

```bash
uv sync --locked --group dev --extra full
```

(`fastapi` / `uvicorn` are included in the `dev` group for tests.)

## Run locally

```bash
uv run doctranslate serve --host 127.0.0.1 --port 8000
```

- OpenAPI UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Authentication

The OSS HTTP API uses a **single shared secret** (opaque string, not a JWT). By default **authentication is disabled** so local scripts and tests keep working unchanged.

| `DOCTRANSLATE_API_AUTH_MODE` | Behavior |
|-----------------------------|----------|
| `disabled` (default) | No credentials required on any route. |
| `required` | Protected routes need **`Authorization: Bearer <token>`** or **`X-API-Key: <token>`** (header name overridable via `DOCTRANSLATE_API_AUTH_HEADER_API_KEY_NAME`). **`DOCTRANSLATE_API_AUTH_TOKEN` must be set** at process start. |

**Public when `auth_mode=required` (default):** `GET /v1/health/live` and `GET /v1/health/ready` stay unauthenticated so orchestrators can probe liveness/readiness without a secret. Set `DOCTRANSLATE_API_AUTH_ALLOW_UNAUTHENTICATED_PROBE_PATHS=false` to require the token on those URLs as well.

**Also protected when `auth_mode=required`:** all other `/v1/*` routes, plus **`GET /metrics`** (when enabled), **`/docs`**, **`/openapi.json`**, and **`/redoc`** (unless `DOCTRANSLATE_API_DOCS_ENABLED=false`). Treat interactive docs and metrics as **operator-only** in production.

### Local development (auth off)

```bash
uv run doctranslate serve --host 127.0.0.1 --port 8000
# no Authorization header needed
curl -sS "http://127.0.0.1:8000/v1/runtime"
```

### Production-style (Bearer)

```bash
export DOCTRANSLATE_API_AUTH_MODE=required
export DOCTRANSLATE_API_AUTH_TOKEN='your-long-random-secret'
uv run doctranslate serve --host 127.0.0.1 --port 8000

curl -sS -H "Authorization: Bearer your-long-random-secret" \
  "http://127.0.0.1:8000/v1/runtime"
```

### API key header (alternative)

```bash
curl -sS -H "X-API-Key: your-long-random-secret" \
  "http://127.0.0.1:8000/v1/runtime"
```

### OpenAPI / Swagger UI

When `auth_mode=required`, open **`/docs`** only with a valid token (same middleware as `/openapi.json`). In Swagger UI use **Authorize** and enter the token for the HTTP Bearer scheme, or send the API key header via your client.

### Reverse proxies and gateways

- Forward **`Authorization`** and/or your configured API key header to the API process.
- Strip any untrusted incoming identity headers at the edge; this OSS mode does **not** trust `X-Forwarded-User` or similar.
- Prefer **TLS termination** at the proxy and keep the token out of query strings and logs.

### Troubleshooting (`401`)

| Symptom | Check |
|---------|--------|
| `401` with `ok: false` and “Authentication required” | Missing `Authorization: Bearer …` or API key header on a protected route. |
| `401` with “Invalid authentication credentials” | Wrong token; compare with `DOCTRANSLATE_API_AUTH_TOKEN`. |
| `401` on `/docs` or `/metrics` | Expected when auth is required; supply the same headers as for `/v1/*`. |
| Process exits at startup | With `auth_mode=required`, `DOCTRANSLATE_API_AUTH_TOKEN` must be non-empty. |

### CORS

CORS is driven by **`DOCTRANSLATE_API_CORS_ALLOW_ORIGINS`** (comma-separated), **`DOCTRANSLATE_API_CORS_ALLOW_METHODS`**, **`DOCTRANSLATE_API_CORS_ALLOW_HEADERS`**, and **`DOCTRANSLATE_API_CORS_ALLOW_CREDENTIALS`**. Default remains permissive (`*`) for local use; for production, set an explicit origin allowlist that includes any browser app origin that must call the API.

## Serverless and multi-instance behavior

Job records live in **SQLite** under `DOCTRANSLATE_API_DATA_ROOT` by default (with optional dual-write to legacy `meta.json` per job). Execution mode is selected with **`DOCTRANSLATE_API_QUEUE_BACKEND`**:

| Mode | Behavior |
|------|----------|
| **`inprocess`** (default) | A bounded-concurrency `JobManager` runs jobs inside the API process (asyncio tasks + semaphore). |
| **`arq`** | The API **enqueues** work to **Redis**; a separate **`doctranslate worker`** process runs translations/warmups. Use **shared** `DOCTRANSLATE_API_DATA_ROOT` (and DB path) across API + workers. See [HTTP API workers](http-api-workers.md). |

Implications:

- **`POST /v1/jobs` returns `202`** with a `job_id`; **`GET /v1/jobs/{id}`** polls SQLite-backed state. With **`inprocess`** and multiple API replicas, clients may need stickiness unless only one replica accepts jobs. With **`arq`**, any replica can serve status as long as metadata/artifacts are shared.
- **Horizontal scaling**: `inprocess` replicas do **not** share an in-memory queue. For production multi-replica APIs, prefer **`arq`** (or an external pattern) plus **object storage** for inputs/outputs when appropriate.
- **Restarts**: completed/failed jobs remain **readable from SQLite** (and disk blobs if `DOCTRANSLATE_API_DATA_ROOT` persists). **`inprocess`**: in-flight tasks do not survive API restart. **`arq`**: queued jobs remain in Redis; a running worker may be restarted independently.

For platform guidance, see [Serverless containers](serverless-containers.md) and [Deploy on Cloud Run](deploy-cloud-run.md).

For **blob mirrors (S3/GCS), presigned downloads, TTL cleanup, and migration** from legacy `meta.json`, see [HTTP API storage and metadata](http-api-storage-backends.md).

## Docker

Build the API image (extends the CPU translate stack + `api` extra):

```bash
docker build --target runtime-api -t doctranslater:api .
docker run --rm -p 8000:8000 \
  -e OPENAI_API_KEY \
  -v doctranslate-cache:/home/doctranslater/.cache/doctranslate \
  -v "$PWD/examples/ci:/in:ro" \
  doctranslater:api
```

Hardened example (shared secret + explicit CORS origin):

```bash
docker run --rm -p 8000:8000 \
  -e OPENAI_API_KEY \
  -e DOCTRANSLATE_API_AUTH_MODE=required \
  -e DOCTRANSLATE_API_AUTH_TOKEN \
  -e DOCTRANSLATE_API_CORS_ALLOW_ORIGINS='https://app.example.com' \
  -v doctranslate-cache:/home/doctranslater/.cache/doctranslate \
  -v "$PWD/examples/ci:/in:ro" \
  doctranslater:api
```

Then create a job (mounted PDF under `/work` — default allow-prefix):

```bash
curl -sS -X POST 'http://127.0.0.1:8000/v1/jobs' \
  -H "Authorization: Bearer $DOCTRANSLATE_API_AUTH_TOKEN" \
  -F 'translation_request={"schema_version":"1","input_pdf":"/work/test.pdf","lang_in":"en","lang_out":"zh","translator":{"mode":"openai","openai":{"model":"gpt-4o-mini"}},"options":{"skip_translation":true}}'
```

Multipart upload variant:

```bash
curl -sS -X POST 'http://127.0.0.1:8000/v1/jobs' \
  -H "Authorization: Bearer $DOCTRANSLATE_API_AUTH_TOKEN" \
  -F 'translation_request={"schema_version":"1","lang_in":"en","lang_out":"zh","translator":{"mode":"openai","openai":{"model":"gpt-4o-mini"}},"options":{"skip_translation":true}}' \
  -F "input_pdf=@examples/ci/test.pdf;type=application/pdf"
```

Poll status and fetch the result:

```bash
JOB_ID=...
curl -sS -H "Authorization: Bearer $DOCTRANSLATE_API_AUTH_TOKEN" \
  "http://127.0.0.1:8000/v1/jobs/$JOB_ID"
curl -sS -H "Authorization: Bearer $DOCTRANSLATE_API_AUTH_TOKEN" \
  "http://127.0.0.1:8000/v1/jobs/$JOB_ID/result"
```

When `DOCTRANSLATE_API_AUTH_MODE` is `disabled` (default), omit the `-H "Authorization: …"` lines.

## Endpoints (v1)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/v1/health/live` | Liveness |
| `GET` | `/v1/health/ready` | Readiness (dirs, optional assets, job capacity, Redis when `arq`) |
| `GET` | `/v1/runtime` | Version and schema versions |
| `GET` | `/v1/assets/status` | Font/model cache presence |
| `POST` | `/v1/assets/warmup` | Async warmup job (`202` + job id) |
| `POST` | `/v1/config/validate` | Validate `TranslationRequest` JSON and/or router/local TOML |
| `POST` | `/v1/inspect` | PDF inspection (`inspect_input`) |
| `POST` | `/v1/jobs` | Create translation job (`202`, multipart or mounted path) |
| `GET` | `/v1/jobs/{id}` | Job status / last progress event (includes `progress_seq`) |
| `GET` | `/v1/jobs/{id}/events` | Replayable progress history (`after_seq`, `limit`) |
| `GET` | `/v1/jobs/{id}/stream` | **SSE** progress stream (`text/event-stream`; supports `Last-Event-ID` reconnect; `full_events=1` includes full `finish` payload) |
| `POST` | `/v1/jobs/{id}/cancel` | Best-effort cancel |
| `GET` | `/v1/jobs/{id}/result` | Result + artifact URLs |
| `GET` | `/v1/jobs/{id}/manifest` | Artifact manifest with resolved download URLs + metadata |
| `GET` | `/v1/jobs/{id}/artifacts/{kind}` | Download one artifact (supports `Range`, optional redirect to presigned URL) |
| `HEAD` | `/v1/jobs/{id}/artifacts/{kind}` | Artifact size / type without downloading the body |

### Progress streams and webhooks

- **Polling** remains supported: `GET /v1/jobs/{id}` is unchanged aside from optional `progress_seq`.
- **Replay**: `GET /v1/jobs/{id}/events?after_seq=N` returns ordered `{seq, event}` rows from SQLite (`job_events` table).
- **SSE**: `curl -N "http://127.0.0.1:8000/v1/jobs/$JOB_ID/stream"` — behind nginx, set `proxy_buffering off` for the location so chunks flush promptly.
- **Webhooks** (optional): add multipart form field `webhook` with JSON `{"url":"https://example.com/hook","secret":"..."}` or `{"url":"...","secret_env":"MY_ENV_VAR"}` (secret read at delivery time). On terminal states the API POSTs a compact JSON body signed with Standard Webhooks–style `webhook-id`, `webhook-timestamp`, and `webhook-signature` (`v1,<hmac>`). Delivery uses retries with exponential backoff until success or max attempts.
- Set **`DOCTRANSLATE_API_PUBLIC_BASE_URL`** when consumers need absolute `result_url` / `manifest_url` values inside webhook payloads (otherwise paths are rooted at `/v1/...` relative to the configured origin).

## Environment variables

| Variable | Default | Meaning |
|----------|---------|---------|
| `DOCTRANSLATE_API_AUTH_MODE` | `disabled` | `disabled` or `required` (shared secret on protected routes) |
| `DOCTRANSLATE_API_AUTH_TOKEN` | *(unset)* | Shared secret when `auth_mode=required` (use a strong random value) |
| `DOCTRANSLATE_API_AUTH_HEADER_API_KEY_NAME` | `X-API-Key` | Header name for API-key style authentication |
| `DOCTRANSLATE_API_AUTH_ALLOW_UNAUTHENTICATED_PROBE_PATHS` | `true` | When `false`, liveness/readiness also require auth |
| `DOCTRANSLATE_API_DOCS_ENABLED` | `true` | Expose `/docs`, `/redoc`, `/openapi.json` |
| `DOCTRANSLATE_API_CORS_ALLOW_ORIGINS` | `*` | Comma-separated allowed origins (see [Authentication](#authentication)) |
| `DOCTRANSLATE_API_CORS_ALLOW_CREDENTIALS` | `false` | CORS `Access-Control-Allow-Credentials` |
| `DOCTRANSLATE_API_CORS_ALLOW_METHODS` | `*` | Comma-separated methods or `*` |
| `DOCTRANSLATE_API_CORS_ALLOW_HEADERS` | `*` | Comma-separated headers or `*` |
| `DOCTRANSLATE_API_DATA_ROOT` | system temp + `/doctranslate-api` | Job workspaces and metadata |
| `DOCTRANSLATE_API_TMP_ROOT` | *(unset)* | Optional separate temp root |
| `DOCTRANSLATE_API_MOUNT_ALLOW_PREFIXES` | `/work,/in,/data` | Allowed path prefixes for `input_pdf` without upload |
| `DOCTRANSLATE_API_ALLOW_MOUNTED_PATHS` | `true` | Disable mounted paths when `false` |
| `DOCTRANSLATE_API_MAX_UPLOAD_BYTES` | `256000000` | Multipart upload limit |
| `DOCTRANSLATE_API_QUEUE_BACKEND` | `inprocess` | `inprocess` or `arq` (Redis workers) |
| `DOCTRANSLATE_API_REDIS_URL` | `redis://127.0.0.1:6379/0` | Redis for ARQ (`queue_backend=arq`) |
| `DOCTRANSLATE_API_ARQ_QUEUE_NAME` | `arq:queue` | ARQ queue name (API + worker must match) |
| `DOCTRANSLATE_API_MAX_CONCURRENT_JOBS` | `2` | Semaphore for **in-process** running jobs; per-worker concurrency hint for `arq` |
| `DOCTRANSLATE_API_MAX_QUEUED_JOBS` | `32` | Max jobs in `queued`+`running` (SQLite count for `arq`) |
| `DOCTRANSLATE_API_JOB_TIMEOUT_SECONDS` | `0` | Per-job wall clock (`0` = off) |
| `DOCTRANSLATE_API_REQUIRE_ASSETS_READY` | `false` | If `true`, readiness requires warmed assets |
| `DOCTRANSLATE_API_WARMUP_ON_STARTUP` | `none` | `none` \| `lazy` \| `eager` (only `eager` is implemented: run `assets.warmup` at startup) |
| `DOCTRANSLATE_API_ARTIFACT_RETENTION_SECONDS` | `86400` | After terminal job states, schedule workspace + metadata deletion (0 disables) |
| `DOCTRANSLATE_API_TTL_CLEANUP_INTERVAL_SECONDS` | `300` | Background sweep interval for expired jobs |
| `DOCTRANSLATE_API_METADATA_SQLITE_PATH` | *(unset)* | Override SQLite DB path (default `<DATA_ROOT>/http_api_metadata.db`) |
| `DOCTRANSLATE_API_DUAL_WRITE_JSON_META` | `true` | Also write `jobs/<id>/meta.json` |
| `DOCTRANSLATE_API_READ_JSON_META_FALLBACK` | `true` | If SQLite misses a row, read legacy `meta.json` |
| `DOCTRANSLATE_API_ARTIFACT_STORAGE` | `local` | `local` or `remote` (fsspec mirror) |
| `DOCTRANSLATE_API_ARTIFACT_REMOTE_ROOT` | *(unset)* | e.g. `s3://bucket/prefix` (requires `[api-s3]`) |
| `DOCTRANSLATE_API_FSSPEC_STORAGE_OPTIONS_JSON` | *(empty)* | JSON object for fsspec / s3fs / gcsfs options |
| `DOCTRANSLATE_API_ARTIFACT_DOWNLOAD_MODE` | `proxy` | `proxy` or `redirect` (presigned URLs when available) |
| `DOCTRANSLATE_API_PRESIGN_EXPIRES_SECONDS` | `3600` | Presigned URL TTL |
| `DOCTRANSLATE_API_JOB_SSE_POLL_INTERVAL_SECONDS` | `0.25` | Poll interval for SSE when not using in-process fan-out (`arq` workers) |
| `DOCTRANSLATE_API_PUBLIC_BASE_URL` | *(unset)* | Optional public origin for webhook payload URLs (`https://api.example.com`) |
| `DOCTRANSLATE_API_WEBHOOK_HTTPS_REQUIRED` | `false` | When `true`, reject non-HTTPS webhook URLs at job creation |
| `DOCTRANSLATE_API_WEBHOOK_ALLOW_HOSTS` | *(empty)* | Optional comma-separated host allowlist for webhook URLs |
| `DOCTRANSLATE_API_WEBHOOK_MAX_ATTEMPTS` | `10` | Max delivery attempts before abandoning a webhook |
| `DOCTRANSLATE_API_WEBHOOK_DELIVERY_BATCH` | `5` | Max concurrent webhook deliveries per sweep |
| `DOCTRANSLATE_API_WEBHOOK_HTTP_TIMEOUT_SECONDS` | `30` | Outbound webhook HTTP timeout |
| `DOCTRANSLATE_API_WEBHOOK_SWEEP_INTERVAL_SECONDS` | `2` | Background sweep interval for pending webhook deliveries |

## Production notes

- Prefer **horizontal scaling** (several single-worker replicas) over many Uvicorn workers per replica: the layout ONNX model and PDF work are memory-heavy.
- Put `DOCTRANSLATE_API_DATA_ROOT` on a writable volume; mount `~/.cache/doctranslate` for persistent fonts/models/TM.
- Configure reverse-proxy `client_max_body_size` to match `DOCTRANSLATE_API_MAX_UPLOAD_BYTES`.
- Enable **`DOCTRANSLATE_API_AUTH_MODE=required`** before exposing the service on the internet; use a long random `DOCTRANSLATE_API_AUTH_TOKEN` from a secret manager.
- Tighten **CORS** to explicit origins; avoid `*` for browser-accessible production APIs.
- Optionally set **`DOCTRANSLATE_API_DOCS_ENABLED=false`** on internet-facing services if you do not want interactive OpenAPI UI reachable.

### Serverless deployment (short checklist)

1. Choose image **`runtime-api`** and container port **8000** (see [Docker image profiles](docker-profiles.md)).
2. Set **`DOCTRANSLATE_API_DATA_ROOT`** (and optionally **`DOCTRANSLATE_API_TMP_ROOT`**) on **fast writable** storage.
3. Decide warmup strategy: baked **warm** image, `DOCTRANSLATE_API_WARMUP_ON_STARTUP=eager`, or `POST /v1/assets/warmup` after deploy.
4. Set **`DOCTRANSLATE_API_JOB_TIMEOUT_SECONDS`** when the platform needs a hard wall-clock bound.
5. For multi-replica services, prefer **`DOCTRANSLATE_API_QUEUE_BACKEND=arq`** with shared storage, or read [Serverless and multi-instance behavior](#serverless-and-multi-instance-behavior) and enable **session affinity** only as a best-effort mitigation for `inprocess`.

Full matrix and image tags: [Serverless runtime & image reference](serverless-runtime-reference.md).

## Observability

Structured JSON logs, Prometheus (`GET /metrics`), request correlation (`X-Request-ID`), and optional OpenTelemetry tracing are documented in **[Observability](observability.md)**.

## ASGI import

Uvicorn can load the pre-built app:

```bash
uvicorn doctranslate.http_api.app:app --host 0.0.0.0 --port 8000
```
