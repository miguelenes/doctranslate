# Serverless runtime and image reference

Quick reference for **environment variables**, **Docker targets**, and **workload compatibility** when deploying DocTranslater on serverless container platforms. Full HTTP field list: [HTTP API – Environment variables](http-api.md#environment-variables).

## Docker image ↔ workload matrix

| Dockerfile target | Published GHCR name (suffix) | Typical role | LLM / ONNX / OCR |
|-------------------|------------------------------|--------------|------------------|
| `runtime-base` | `doctranslater-base` | Schemas, light CLI | No PDF / no ONNX |
| `runtime-cpu` | `doctranslater-cpu` | CLI translate, **worker** jobs | PDF + layout ONNX + LLM; no `full` OCR/Hyperscan by default |
| `runtime-cpu-warm` | *(build locally / custom registry)* | Same as CPU, **baked cache** | Same; faster cold start |
| `runtime-api` | `doctranslater-api` | **HTTP service** | Same Python extras as CPU + **`api`** |
| `runtime-vision` | `doctranslater-vision` | CLI / worker **full** stack | OCR + Hyperscan glossary path + `full` |
| `runtime-vision-warm` | *(build locally / custom registry)* | Full stack + **baked cache** | Same; faster cold start |

**Tags** (on `main`): `main`, `sha-<short>`; **`latest`** applies only to **`doctranslater-cpu`** — see [Docker – Prebuilt images](docker.md#prebuilt-images-github-container-registry).

**Python version**: images default to **Python 3.12** (`Dockerfile` `ARG PYTHON_VERSION=3.12`), within `requires-python = ">=3.10,<3.14"` in [`pyproject.toml`](https://github.com/miguelenes/doctranslate/blob/main/pyproject.toml).

## HTTP API environment variables (serverless-focused)

| Variable | Default | Serverless notes |
|----------|---------|-------------------|
| `DOCTRANSLATE_API_DATA_ROOT` | `{tmpdir}/doctranslate-api` | Use fast local disk or a **mounted volume**; required writable for jobs |
| `DOCTRANSLATE_API_TMP_ROOT` | *(unset → `data_root/tmp`)* | Optional split for scratch I/O |
| `DOCTRANSLATE_API_MOUNT_ALLOW_PREFIXES` | `/work,/in,/data` | Narrow prefixes in multi-tenant deploys |
| `DOCTRANSLATE_API_ALLOW_MOUNTED_PATHS` | `true` | Set `false` if only multipart uploads allowed |
| `DOCTRANSLATE_API_MAX_UPLOAD_BYTES` | `256000000` | Match reverse proxy / API gateway body limits |
| `DOCTRANSLATE_API_MAX_CONCURRENT_JOBS` | `2` | Lower when memory constrained (ONNX + PDF) |
| `DOCTRANSLATE_API_MAX_QUEUED_JOBS` | `32` | Back-pressure; returns **503** when full |
| `DOCTRANSLATE_API_JOB_TIMEOUT_SECONDS` | `0` (off) | Set in serverless to avoid runaway tasks |
| `DOCTRANSLATE_API_REQUIRE_ASSETS_READY` | `false` | Set `true` when readiness must wait for fonts/models |
| `DOCTRANSLATE_API_WARMUP_ON_STARTUP` | `none` | `eager` runs `assets.warmup` at startup (**only `eager` is implemented** for startup; `lazy` is not) |

`DOCTRANSLATE_API_ARTIFACT_RETENTION_SECONDS` exists in settings but **TTL cleanup is not implemented** in the HTTP layer—plan retention at the storage layer (object lifecycle rules) or periodic GC outside the app.

## CLI / engine secrets (not HTTP-specific)

Hosted LLM usage still expects keys via CLI flags, env, or TOML `api_key_env` ([Configuration](configuration.md)). **Never** commit secrets; use platform secret managers.

## Compatibility notes

- **User ID**: images run as **`doctranslater` (UID 1000)** — volume mounts must be writable by that user ([Docker – Troubleshooting](docker.md#permission-denied-on-cache-or-output)).
- **Hyperscan**: `runtime-cpu` does **not** install `libhyperscan5`; use **`runtime-vision`** or extend the Dockerfile ([Docker profiles](docker-profiles.md)).
- **Read-only root**: mount writable paths for cache and job dirs ([Docker – Security](docker.md#security)).

## Related guides

- [Serverless containers](serverless-containers.md)
- [Deploy on Cloud Run](deploy-cloud-run.md)
- [Deploy on Fargate and App Runner](deploy-fargate-app-runner.md)
- [Modal and Runpod](deploy-modal-runpod.md)
