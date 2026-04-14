# API

DocTranslater provides an optional HTTP API for document translation workflows.
The API is implemented with FastAPI and exposed under the `/v1` prefix.

For full deployment and storage/backend details, see `docs/http-api.md`.

## Run the API

```bash
uv run doctranslate serve --host 127.0.0.1 --port 8000
```

- OpenAPI UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Core Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/v1/health/live` | Liveness probe (`{"status":"ok"}`) |
| `GET` | `/v1/health/ready` | Readiness checks (writable paths, queue health, optional assets check) |
| `GET` | `/v1/runtime` | Runtime metadata (package/schema/python versions, cache dir) |
| `GET` | `/v1/assets/status` | Asset cache presence/verification |
| `POST` | `/v1/assets/warmup` | Queue an async warmup job (`202`) |
| `POST` | `/v1/config/validate` | Validate `translation_request` and/or translator config |
| `POST` | `/v1/inspect` | Inspect input PDFs without translation |
| `POST` | `/v1/jobs` | Create translation job (`202`) using multipart upload or mounted path |
| `GET` | `/v1/jobs/{job_id}` | Read job status/progress |
| `POST` | `/v1/jobs/{job_id}/cancel` | Best-effort job cancellation (`204`) |
| `GET` | `/v1/jobs/{job_id}/result` | Read result envelope + artifact links |
| `GET` | `/v1/jobs/{job_id}/artifacts/{kind}` | Download/stream one artifact (supports `Range`) |

## Typical Job Flow

1. `POST /v1/jobs` to enqueue work.
2. Poll `GET /v1/jobs/{job_id}` until terminal state (`succeeded`, `failed`, `canceled`).
3. `GET /v1/jobs/{job_id}/result` to get result details and artifact URLs.
4. Optionally download specific files via `/v1/jobs/{job_id}/artifacts/{kind}`.

## Create a Translation Job

`POST /v1/jobs` expects multipart form-data:

- `translation_request` (**required**): JSON string of a `TranslationRequest`.
- `input_pdf` (**optional**): uploaded PDF file.

If `input_pdf` is omitted, `translation_request.input_pdf` must point to an allowed mounted path.

### Example: uploaded PDF

```bash
curl -sS -X POST "http://127.0.0.1:8000/v1/jobs" \
  -F 'translation_request={"schema_version":"1","lang_in":"en","lang_out":"zh","translator":{"mode":"openai","openai":{"model":"gpt-4o-mini"}},"options":{"skip_translation":true}}' \
  -F "input_pdf=@examples/ci/test.pdf;type=application/pdf"
```

### Example response (`202 Accepted`)

```json
{
  "job_id": "3d8a6b35-2a3a-4c2d-a35a-2f9f56d1c7ee",
  "kind": "translation",
  "state": "queued",
  "status_url": "http://127.0.0.1:8000/v1/jobs/3d8a6b35-2a3a-4c2d-a35a-2f9f56d1c7ee"
}
```

## Job States and Kinds

- Job states: `queued`, `running`, `succeeded`, `failed`, `canceled`
- Job kinds: `translation`, `warmup`

## Error Shape

Error responses use a consistent JSON envelope (`ApiErrorEnvelope`) with:

- `ok: false`
- `schema_version`
- optional `request_id`
- `error` object (`code`, `message`, `retryable`, and optional details)

Common statuses include:

- `400` invalid JSON/input
- `404` unknown job/artifact
- `413` upload exceeds configured max size
- `422` validation failure
- `503` queue at capacity / service busy

## Important Notes

- `POST /v1/jobs` always returns `202` on accept; execution is asynchronous.
- Configure backend and storage behavior via environment variables (queue backend, retention, artifact mode, Redis, etc.); see `docs/http-api.md` for the complete matrix.
- For artifact redirects/presigned URLs and remote storage behavior, see `docs/http-api-storage-backends.md`.
