# Docker image profiles

Build from the repository root with `-f Dockerfile`. The [`Dockerfile`](https://github.com/miguelenes/doctranslate/blob/main/Dockerfile) lives at the repo root.

| Build target | Python extras | Typical use |
|--------------|---------------|-------------|
| `runtime-base` | (none) | Schemas, `doctranslate config`, light tooling |
| `runtime-cpu` | `pdf`, `cli`, `llm`, `tm`, `vision` | CLI/API translation without `full` OCR/Hyperscan stack |
| `runtime-api` | same as `runtime-cpu` + `api` | HTTP API service (`doctranslate serve`, port **8000**) |
| `runtime-cpu-warm` | same as `runtime-cpu` | Pre-downloaded fonts/models/cmaps under `~/.cache/doctranslate` |
| `runtime-vision` | `full` | Parity with default CI install (OCR, glossary acceleration, vision) |
| `runtime-vision-warm` | same as `runtime-vision` | Warm asset cache baked in |
| `runtime-dev` | `full` + `[dependency-groups] dev` | Pytest, Ruff, MkDocs in container |

## Serverless / deployment role mapping

Use this table when choosing a **service** vs **worker** image for managed platforms ([Serverless containers](serverless-containers.md)).

| Deployment role | Dockerfile target | Notes |
|-----------------|--------------------|-------|
| HTTP API (FastAPI / Uvicorn) | `runtime-api` | Default `CMD` is `serve` on port **8000** |
| Batch / queue worker (CLI) | `runtime-cpu` or `runtime-vision` | Run `doctranslate translate …` or embed `doctranslate.api` |
| Lowest cold-start (CPU stack) | `runtime-cpu-warm` | Pre-populated `~/.cache/doctranslate` in the image |
| Full stack + lowest cold-start | `runtime-vision-warm` | CI-parity extras + baked cache |

## Build arguments

| ARG | Default | Stages | Meaning |
|-----|---------|--------|---------|
| `PYTHON_VERSION` | `3.12` | all | Must match a supported interpreter (3.10–3.13). |
| `INCLUDE_OCR` | `0` | `builder-cpu-sync` | Add `ocr` extra to the CPU image. |
| `INCLUDE_GLOSSARY` | `0` | `builder-cpu-sync` | Add `glossary` extra (Hyperscan); runtime already has `libhyperscan` only on vision targets — if you enable this, extend the **runtime** `apt` layer with `libhyperscan5` or use `runtime-vision`. |

CPU runtime **omits** `libhyperscan5` by default. Use `runtime-vision` for Hyperscan-backed glossary scanning, or customize the Dockerfile `apt-get` list if you build CPU with `INCLUDE_GLOSSARY=1`.

## Examples

```bash
docker build --target runtime-cpu -t doctranslater:cpu .
docker build --target runtime-api -t doctranslater:api .
docker build --target runtime-vision-warm -t doctranslater:vision-warm .
docker build --target runtime-dev -t doctranslater:dev .
```

Warm targets need network access during `docker build` for `doctranslate assets warmup`.

See [Docker overview](docker.md) for run examples, volumes, and environment variables.
