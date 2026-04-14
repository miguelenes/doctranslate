# Modal and Runpod

Optional platforms for **GPU**, **burst workers**, or **pod-style** execution. This repo does not ship proprietary orchestration; integration is **your** Modal app or Runpod template calling the same containers / CLI documented in [Docker](docker.md).

## Modal

**Fit**: **Strong** for async translation workers (queue + `modal.Function` / `.map`), custom images, and volume mounts for caches.

**Pattern**:

1. Build or reference a base image derived from `runtime-cpu` / `runtime-vision` (see [Docker image profiles](docker-profiles.md) and the repo [`Dockerfile`](https://github.com/miguelenes/doctranslate/blob/main/Dockerfile)).
2. Run `doctranslate translate` with input/output on Modal volumes or download/upload from object storage.
3. Keep **secrets** (API keys) in Modal secrets, not in images.

**Why not the primary OSS doc target**: Modal uses Python-first APIs; many users want plain **Docker + YAML** first—see [Deploy on Cloud Run](deploy-cloud-run.md).

## Runpod

**Fit**: **Possible** — useful when you want **GPU** (e.g. ONNX GPU extras in [`pyproject.toml`](https://github.com/miguelenes/doctranslate/blob/main/pyproject.toml) `cuda` / `directml`) or per-job pods with large disks.

**Pattern**:

- Container image: `runtime-vision` for full optional stack (OCR, Hyperscan glossary path) or custom `runtime-cpu` with `INCLUDE_OCR=1` (see [`pyproject.toml` optional extras](https://github.com/miguelenes/doctranslate/blob/main/pyproject.toml)).
- Mount host or network volume for `~/.cache/doctranslate` where supported.
- Drive jobs via Runpod serverless **handler** that shells `doctranslate translate` or imports `doctranslate.api`.

## Related

- [Serverless containers](serverless-containers.md)
- [Serverless runtime & image reference](serverless-runtime-reference.md)
