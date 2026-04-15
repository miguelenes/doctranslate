# DocTranslater edge API (Cloudflare Python Worker)

Thin **Python Worker** that validates `translation_request` against `doctranslate.schemas.public_api` (not the `doctranslate.schemas` package barrel) and forwards the same multipart payload to a full **DocTranslater HTTP API** (`POST /v1/jobs`). The PDF/ONNX pipeline does not run in Pyodide; see [ARCHITECTURE.md](ARCHITECTURE.md).

## Prerequisites

- Python 3.12 or 3.13
- [uv](https://docs.astral.sh/uv/)
- Node.js (for Wrangler schema and `npm run dev`)

## Setup

```bash
cd workers/edge-api
npm install
uv sync --group dev
```

## Local dev (Worker runtime)

Set the upstream base URL (no trailing `/v1/jobs`; the worker appends `/v1/jobs`).

```bash
cp .dev.vars.example .dev.vars   # then edit DOCTRANSLATE_UPSTREAM_URL
# or set vars in wrangler.jsonc / dashboard
uv run pywrangler dev
```

The file `.dev.vars` is gitignored. Edit `wrangler.jsonc` `vars.DOCTRANSLATE_UPSTREAM_URL` to point at a running `doctranslate serve` instance, or configure the variable in the Cloudflare dashboard for deploys.

## Tests

```bash
cd workers/edge-api
uv run pytest tests/ -q
```

## Deploy

### Pre-flight (local)

```bash
cd workers/edge-api
npm install
uv sync --group dev
uv run pytest tests/ -q
npm run deploy:dry-run   # validates wrangler.jsonc and bundles without uploading
```

### Cloudflare dashboard

1. Create or select a Worker; set **Variables** (production / preview as needed):
   - `DOCTRANSLATE_UPSTREAM_URL` — base URL of the DocTranslater HTTP API (no `/v1/jobs` suffix), e.g. `https://api.internal`.
2. Optionally set `UPSTREAM_URL` instead (same semantics as in code).
3. Use **Secrets** only for operator-held values; clients often send `Authorization` on each request, which the worker forwards upstream unchanged.

### Publish

```bash
cd workers/edge-api
npm run deploy
# or: uv run pywrangler deploy
```

After deploy, verify `GET /health` and `GET /edge/v1/schema-warmup` on your worker route, then `POST /edge/v1/jobs` against a non-production upstream.

### Behaviour notes

- **502** `{"detail":"upstream request failed"}` — connection/timeout or other `httpx` transport failure to the upstream (see worker logs).
- **503** — `DOCTRANSLATE_UPSTREAM_URL` / `UPSTREAM_URL` not set in the Worker environment.

Ensure secrets (upstream API keys forwarded from clients, or operator tokens) follow your security model; the worker forwards the `Authorization` header to the upstream when present.

## Routes

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| GET | `/edge/v1/schema-warmup` | Import `public_api` / `versions` only (Pyodide smoke) |
| POST | `/edge/v1/jobs` | Validate multipart, proxy to upstream `POST /v1/jobs` |
