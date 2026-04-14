# HTTP API storage and metadata

The optional HTTP API persists **job metadata** (state, progress, errors, `TranslationResult`) separately from **blobs** (uploaded PDFs and generated artifacts). Defaults keep a **zero-infra** layout on local disk; optional settings mirror blobs to **S3-compatible** or **GCS** URLs via [fsspec](https://filesystem-spec.readthedocs.io/).

## Defaults (OSS / local dev)

| Plane | Behavior |
|-------|----------|
| Metadata | SQLite at `<DOCTRANSLATE_API_DATA_ROOT>/http_api_metadata.db` |
| Blobs | Local directories `<DOCTRANSLATE_API_DATA_ROOT>/jobs/<job_id>/{input,work,output}` |
| Legacy | If `DOCTRANSLATE_API_DUAL_WRITE_JSON_META=true`, `meta.json` is still written beside each job for compatibility |

The translation engine still runs against **local paths**; remote modes **upload outputs after** a job finishes.

## Metadata migration

To import existing `jobs/*/meta.json` files into SQLite (for example after an upgrade):

```bash
uv run python -m doctranslate.http_api.migrate_metadata \
  --data-root /path/to/doctranslate-api-data
```

Optional: `--sqlite-path /custom/path.db`.

## Remote blob mirror (fsspec)

Set:

| Variable | Meaning |
|----------|---------|
| `DOCTRANSLATE_API_ARTIFACT_STORAGE` | `local` (default) or `remote` |
| `DOCTRANSLATE_API_ARTIFACT_REMOTE_ROOT` | fsspec URL root, e.g. `s3://mybucket/prefix` or `file:///tmp/remote-test` |
| `DOCTRANSLATE_API_FSSPEC_STORAGE_OPTIONS_JSON` | JSON object of storage options (S3 keys, `client_kwargs`, `endpoint_url`, …) |

Install optional extras as needed:

- **S3 / MinIO / R2:** `pip install "DocTranslater[api,api-s3]"` (pulls `s3fs`, `boto3`).
- **GCS:** `pip install "DocTranslater[api,api-gcs]"` (pulls `gcsfs`).

## Downloads

| Variable | Meaning |
|----------|---------|
| `DOCTRANSLATE_API_ARTIFACT_DOWNLOAD_MODE` | `proxy` (default): API streams bytes; `redirect`: `/result` and direct artifact GET may use **presigned** URLs when credentials allow |
| `DOCTRANSLATE_API_PRESIGN_EXPIRES_SECONDS` | Presigned URL lifetime (default `3600`) |

`GET /v1/jobs/{id}/artifacts/{kind}` supports `Range: bytes=…` for **local** files and **remote** objects opened via fsspec.

## TTL cleanup

| Variable | Meaning |
|----------|---------|
| `DOCTRANSLATE_API_ARTIFACT_RETENTION_SECONDS` | After a job reaches a terminal state (`succeeded`, `failed`, `canceled`), metadata gets an expiry; the background sweep deletes SQLite rows, optional `meta.json`, local workspace, and remote `jobs/<id>` prefix when due. `0` disables TTL. |
| `DOCTRANSLATE_API_TTL_CLEANUP_INTERVAL_SECONDS` | Sweep interval (default `300`) |

## Multi-replica note

SQLite metadata is **per host file** unless the database file lives on **shared storage**. For multiple API replicas sharing job state, run an external database (for example Postgres) in your own deployment layer or accept single-replica semantics; the OSS tree ships SQLite as the portable default.

## Related

- [HTTP API](http-api.md) — endpoints and core environment variables
- [Docker](docker.md) — volumes and cache paths
