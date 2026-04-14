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

## Serverless and multi-instance behavior

The HTTP API uses an **in-process** `JobManager` (bounded concurrency). Job records live in **SQLite** under `DOCTRANSLATE_API_DATA_ROOT` by default (with optional dual-write to legacy `meta.json` per job). That implies:

- **`POST /v1/jobs` returns `202`** with a `job_id`; **`GET /v1/jobs/{id}`** polls state on **that same container instance** unless you add infrastructure that pins the client to the instance (e.g. Cloud Run **session affinity**, ALB **stickiness**).
- **Horizontal scaling** adds replicas that **do not share** the in-memory queue. For production multi-replica APIs, prefer an **external job queue** and **object storage** for inputs/outputs, put the SQLite DB on **shared storage** if you need shared metadata, or accept single-replica semantics.
- **Restarts**: completed/failed jobs remain **readable from SQLite** (and disk blobs if `DOCTRANSLATE_API_DATA_ROOT` persists); **in-flight** tasks do not survive process restart.

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

Then create a job (mounted PDF under `/work` — default allow-prefix):

```bash
curl -sS -X POST 'http://127.0.0.1:8000/v1/jobs' \
  -F 'translation_request={"schema_version":"1","input_pdf":"/work/test.pdf","lang_in":"en","lang_out":"zh","translator":{"mode":"openai","openai":{"model":"gpt-4o-mini"}},"options":{"skip_translation":true}}'
```

Multipart upload variant:

```bash
curl -sS -X POST 'http://127.0.0.1:8000/v1/jobs' \
  -F 'translation_request={"schema_version":"1","lang_in":"en","lang_out":"zh","translator":{"mode":"openai","openai":{"model":"gpt-4o-mini"}},"options":{"skip_translation":true}}' \
  -F "input_pdf=@examples/ci/test.pdf;type=application/pdf"
```

Poll status and fetch the result:

```bash
JOB_ID=...
curl -sS "http://127.0.0.1:8000/v1/jobs/$JOB_ID"
curl -sS "http://127.0.0.1:8000/v1/jobs/$JOB_ID/result"
```

## Endpoints (v1)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/v1/health/live` | Liveness |
| `GET` | `/v1/health/ready` | Readiness (dirs, optional assets, job capacity) |
| `GET` | `/v1/runtime` | Version and schema versions |
| `GET` | `/v1/assets/status` | Font/model cache presence |
| `POST` | `/v1/assets/warmup` | Async warmup job (`202` + job id) |
| `POST` | `/v1/config/validate` | Validate `TranslationRequest` JSON and/or router/local TOML |
| `POST` | `/v1/inspect` | PDF inspection (`inspect_input`) |
| `POST` | `/v1/jobs` | Create translation job (`202`, multipart or mounted path) |
| `GET` | `/v1/jobs/{id}` | Job status / last progress event |
| `POST` | `/v1/jobs/{id}/cancel` | Best-effort cancel |
| `GET` | `/v1/jobs/{id}/result` | Result + artifact URLs |
| `GET` | `/v1/jobs/{id}/artifacts/{kind}` | Download one artifact (supports `Range`, optional redirect to presigned URL) |

## Environment variables

| Variable | Default | Meaning |
|----------|---------|---------|
| `DOCTRANSLATE_API_DATA_ROOT` | system temp + `/doctranslate-api` | Job workspaces and metadata |
| `DOCTRANSLATE_API_TMP_ROOT` | *(unset)* | Optional separate temp root |
| `DOCTRANSLATE_API_MOUNT_ALLOW_PREFIXES` | `/work,/in,/data` | Allowed path prefixes for `input_pdf` without upload |
| `DOCTRANSLATE_API_ALLOW_MOUNTED_PATHS` | `true` | Disable mounted paths when `false` |
| `DOCTRANSLATE_API_MAX_UPLOAD_BYTES` | `256000000` | Multipart upload limit |
| `DOCTRANSLATE_API_MAX_CONCURRENT_JOBS` | `2` | Semaphore for running jobs |
| `DOCTRANSLATE_API_MAX_QUEUED_JOBS` | `32` | Max jobs in `queued`+`running` |
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

## Production notes

- Prefer **horizontal scaling** (several single-worker replicas) over many Uvicorn workers per replica: the layout ONNX model and PDF work are memory-heavy.
- Put `DOCTRANSLATE_API_DATA_ROOT` on a writable volume; mount `~/.cache/doctranslate` for persistent fonts/models/TM.
- Configure reverse-proxy `client_max_body_size` to match `DOCTRANSLATE_API_MAX_UPLOAD_BYTES`.

### Serverless deployment (short checklist)

1. Choose image **`runtime-api`** and container port **8000** (see [Docker image profiles](docker-profiles.md)).
2. Set **`DOCTRANSLATE_API_DATA_ROOT`** (and optionally **`DOCTRANSLATE_API_TMP_ROOT`**) on **fast writable** storage.
3. Decide warmup strategy: baked **warm** image, `DOCTRANSLATE_API_WARMUP_ON_STARTUP=eager`, or `POST /v1/assets/warmup` after deploy.
4. Set **`DOCTRANSLATE_API_JOB_TIMEOUT_SECONDS`** when the platform needs a hard wall-clock bound.
5. For multi-replica services, read [Serverless and multi-instance behavior](#serverless-and-multi-instance-behavior) and enable **session affinity** only as a best-effort mitigation.

Full matrix and image tags: [Serverless runtime & image reference](serverless-runtime-reference.md).

## ASGI import

Uvicorn can load the pre-built app:

```bash
uvicorn doctranslate.http_api.app:app --host 0.0.0.0 --port 8000
```
