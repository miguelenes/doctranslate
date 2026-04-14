# HTTP API workers (ARQ + Redis)

When `DOCTRANSLATE_API_QUEUE_BACKEND=arq`, the API process **only enqueues** jobs to Redis; a separate **worker** process runs translations and asset warmups. Job metadata stays in SQLite (`DOCTRANSLATE_API_METADATA_SQLITE_PATH` or default under `DOCTRANSLATE_API_DATA_ROOT`); artifacts use the same [HTTP API storage](http-api-storage-backends.md) settings as the API.

**Live progress:** `GET /v1/jobs/{id}/stream` (SSE) and `GET /v1/jobs/{id}/events` read from the shared SQLite `job_events` table written by workers. There is no in-process fan-out across replicas—any API instance can serve the stream by polling metadata.

## Requirements

- `DocTranslater[api]` (includes `arq` and `redis`).
- A reachable **Redis** instance.
- **Shared** `DOCTRANSLATE_API_DATA_ROOT` (or equivalent object storage + DB paths) between API and worker containers so both see the same job workspaces and SQLite file.

## Environment variables

| Variable | Default | Meaning |
|----------|---------|---------|
| `DOCTRANSLATE_API_QUEUE_BACKEND` | `inprocess` | `inprocess` \| `arq` |
| `DOCTRANSLATE_API_REDIS_URL` | `redis://127.0.0.1:6379/0` | Redis URL for ARQ |
| `DOCTRANSLATE_API_ARQ_QUEUE_NAME` | `arq:queue` | Queue name; **must match** API and worker |

All other `DOCTRANSLATE_API_*` settings (data root, artifact mirror, timeouts, mount prefixes, etc.) apply to **both** processes.

## Running the worker

From the same environment as the API (same `DOCTRANSLATE_API_*` values):

```bash
uv run doctranslate worker
```

Batch / CI style (drain the queue then exit):

```bash
uv run doctranslate worker --burst
```

Equivalent ARQ CLI (same `WorkerSettings`):

```bash
uv run arq doctranslate.http_api.worker.arq_worker.WorkerSettings
```

## Docker Compose (minimal)

Run **Redis**, **one API** replica, and **one or more workers**. Mount the same volume for `DOCTRANSLATE_API_DATA_ROOT` on API and worker. Example sketch:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
  api:
    image: doctranslater:api
    environment:
      DOCTRANSLATE_API_QUEUE_BACKEND: arq
      DOCTRANSLATE_API_REDIS_URL: redis://redis:6379/0
      DOCTRANSLATE_API_DATA_ROOT: /data
    volumes: [ "api-data:/data" ]
    ports: ["8000:8000"]
    depends_on: [redis]
  worker:
    image: doctranslater:api
    command: ["doctranslate", "worker"]
    environment:
      DOCTRANSLATE_API_QUEUE_BACKEND: arq
      DOCTRANSLATE_API_REDIS_URL: redis://redis:6379/0
      DOCTRANSLATE_API_DATA_ROOT: /data
    volumes: [ "api-data:/data" ]
    depends_on: [redis]
volumes:
  api-data:
```

Scale `worker` replicas for throughput; tune `DOCTRANSLATE_API_MAX_CONCURRENT_JOBS` per worker container memory.

## Cancellation and readiness

- `POST /v1/jobs/{id}/cancel` records a cancel request in SQLite and signals ARQ **abort** (best-effort). Cooperative cancel is also checked during progress streaming in the worker.
- `GET /v1/health/ready` includes `job_queue_healthy`: it pings Redis when `queue_backend=arq`.

## Local development

Default remains **`inprocess`** (no Redis). To try ARQ locally:

1. Start Redis (`docker run --rm -p 6379:6379 redis:7-alpine`).
2. Export `DOCTRANSLATE_API_QUEUE_BACKEND=arq` and `DOCTRANSLATE_API_REDIS_URL=redis://127.0.0.1:6379/0`.
3. Run `uv run doctranslate serve` in one terminal and `uv run doctranslate worker` in another (same `DOCTRANSLATE_API_DATA_ROOT`).

## Observability

Workers run in a **separate process** from the API: configure the same `DOCTRANSLATE_*` logging and metrics environment variables, scrape metrics per process, and rely on persisted **`traceparent`** on queued jobs for distributed traces when OTLP is enabled. See [Observability](observability.md).

## See also

- [HTTP API](http-api.md) — endpoints and env reference
- [Docker](docker.md) — image targets
- [Serverless containers](serverless-containers.md) — deployment modes
