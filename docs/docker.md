# Docker

Run DocTranslater in Linux containers for local use, CI, or deployment. Images are defined in the repository [`Dockerfile`](https://github.com/miguelenes/doctranslate/blob/main/Dockerfile). Build targets and `ARG`s are listed in [Docker image profiles](docker-profiles.md).

## Requirements

- Docker 23+ with BuildKit (`DOCKER_BUILDKIT=1`).
- Linux `amd64` or `arm64` (buildx for multi-arch: `docker buildx build --platform linux/amd64,linux/arm64 …`).

## Serverless containers

For **Cloud Run**, **ECS Fargate**, **App Runner**, **Modal**, **Runpod**, and related patterns (image choice, warm assets, ephemeral disk, worker vs HTTP service), see:

- [Serverless containers](serverless-containers.md) — platform matrix and architecture
- [Serverless runtime & image reference](serverless-runtime-reference.md) — env vars and workload ↔ image matrix
- [Deploy on Cloud Run](deploy-cloud-run.md) — primary reference
- [Deploy on Fargate and App Runner](deploy-fargate-app-runner.md)
- Example manifests: [Deploy samples](deploy-samples/README.md) (`cloud-run-service.sample.yaml`, `ecs-taskdef-api.sample.yaml`)

**Profiles:** use **`runtime-api`** for the optional HTTP service; **`runtime-cpu`** / **`runtime-vision`** for CLI or worker-style batch. Warm variants (`runtime-cpu-warm`, `runtime-vision-warm`) reduce runtime downloads but need **network at image build** time.

## Prebuilt images (GitHub Container Registry)

On push to `main`, [`.github/workflows/docker.yml`](https://github.com/miguelenes/doctranslate/blob/main/.github/workflows/docker.yml) builds and pushes **amd64** images to **GitHub Packages** (`ghcr.io`). Use your GitHub username or organization name in **lowercase** as `OWNER` (GHCR requires a lowercase owner in the image path).

| Image | Dockerfile target | Typical use |
|-------|-------------------|-------------|
| `ghcr.io/OWNER/doctranslater-base` | `runtime-base` | Schemas / minimal CLI |
| `ghcr.io/OWNER/doctranslater-cpu` | `runtime-cpu` | Default translate path (PDF + LLM + layout ONNX) |
| `ghcr.io/OWNER/doctranslater-vision` | `runtime-vision` | Full optional stack (OCR, Hyperscan glossary path, …) |
| `ghcr.io/OWNER/doctranslater-api` | `runtime-api` | HTTP API (`serve` on port 8000); see [HTTP API](http-api.md). |
| `ghcr.io/OWNER/doctranslater-dev` | `runtime-dev` | Development / CI parity |

**Tags**

- `main` — tip of the default branch when the workflow ran.
- `sha-<short>` — commit SHA for reproducible pulls.
- `latest` — only on **`doctranslater-cpu`** (the default runtime profile).

**Pull and run** (example for this fork; replace `OWNER` if you use a fork):

```bash
docker pull ghcr.io/miguelenes/doctranslater-cpu:main
docker run --rm ghcr.io/miguelenes/doctranslater-cpu:main --help
```

Private packages require `docker login ghcr.io` (PAT with `read:packages`, or `GITHUB_TOKEN` in CI). For anonymous pulls, keep the package visibility **public** in the repo’s Packages settings.

## Build targets

| Target | Contents |
|--------|----------|
| `runtime-base` | Base PyPI dependencies only (`doctranslate.schemas`, minimal CLI). |
| `runtime-cpu` | PDF + CLI + LLM + TM + **vision** (layout ONNX). No `full` meta-extra; no Hyperscan in the default runtime layer. |
| `runtime-cpu-warm` | Same as `runtime-cpu` with fonts/models/cmaps pre-populated under `/home/doctranslater/.cache/doctranslate`. |
| `runtime-api` | Same Python extras as `runtime-cpu` plus **`api`** (FastAPI/Uvicorn); default `CMD` is `serve` on port **8000**. See [HTTP API](http-api.md). |
| `runtime-vision` | `DocTranslater[full]` — matches default CI optional stack (OCR, Hyperscan glossary path, etc.). |
| `runtime-vision-warm` | Same as `runtime-vision` with warm cache. |
| `runtime-dev` | `full` + dev dependencies (pytest, ruff, mkdocs, …). |

**Why `runtime-cpu` includes `vision`:** the default translate path loads the doclayout ONNX model unless you use an RPC doclayout flag. Install only `pdf`+`cli`+`llm` without `vision` is not sufficient for typical `doctranslate translate` runs.

**OCR-heavy workloads:** use `runtime-vision` (includes `ocr`) or rebuild `runtime-cpu` with `--build-arg INCLUDE_OCR=1` and extend system packages if needed.

## Quick start

Build the CPU image:

```bash
docker build --target runtime-cpu -t doctranslater:cpu .
```

Show CLI help (default command):

```bash
docker run --rm doctranslater:cpu
```

Translate a PDF (mount input/output and pass secrets at runtime, not in the image):

```bash
docker run --rm \
  -e OPENAI_API_KEY \
  -v "$PWD/examples/ci:/in:ro" \
  -v "$PWD/out:/out" \
  doctranslater:cpu \
  translate /in/test.pdf --provider openai \
  --source-lang en --target-lang zh -o /out
```

Router or local mode with TOML on the host:

```bash
docker run --rm \
  -v "$PWD:/work" \
  -w /work \
  doctranslater:cpu \
  translate ./doc.pdf --translator router -c ./doctranslate.toml -o ./out
```

Mount a persistent cache (models, fonts, TM SQLite, tiktoken cache):

```bash
docker run --rm \
  -v doctranslate-cache:/home/doctranslater/.cache/doctranslate \
  doctranslater:cpu-warm \
  translate /in/doc.pdf --provider openai --source-lang en --target-lang zh -o /out
```

Warm assets at runtime (slim images):

```bash
docker run --rm \
  -v doctranslate-cache:/home/doctranslater/.cache/doctranslate \
  doctranslater:vision \
  assets warmup
```

Air-gapped or pinned asset trees: use `doctranslate assets pack-offline` / `restore-offline` (see [Verification](ai/verification.md) and CI in `.github/workflows/test.yml`).

## Entrypoint and signals

The image entrypoint runs [`tini`](https://github.com/krallin/tini) so PID 1 forwards `SIGTERM`/`SIGINT` to the CLI. Override the command after the image name as usual.

An **optional** HTTP API is included (`DocTranslater[api]`); see [HTTP API](http-api.md), [HTTP API workers](http-api-workers.md) (Redis + `doctranslate worker` when `DOCTRANSLATE_API_QUEUE_BACKEND=arq`), [HTTP API storage](http-api-storage-backends.md), and the `runtime-api` image target. You can still embed with `doctranslate.api` from your own process or wrap the CLI.

## Health checks

Images declare `HEALTHCHECK` using `doctranslate --version`. For readiness that includes downloaded assets, use a warm target or mount a populated cache volume.

For HTTP services (`runtime-api`), you can also scrape **`/metrics`** and ship JSON logs from stdout when observability is enabled; see [Observability](observability.md).

## Security

- Images run as user `doctranslater` (UID **1000**).
- Do not bake API keys into images; use `-e` / secrets and `api_key_env` in TOML ([Configuration](configuration.md)).
- For read-only root filesystems, mount writable volumes for `HOME/.cache/doctranslate`, job output (`-o`), and optional `--working-dir`.

### HTTP API (`runtime-api`)

The optional HTTP API supports a **shared secret** for inbound requests (separate from LLM provider keys). See [HTTP API — Authentication](http-api.md#authentication).

```bash
docker run --rm -p 8000:8000 \
  -e DOCTRANSLATE_API_AUTH_MODE=required \
  -e DOCTRANSLATE_API_AUTH_TOKEN \
  -e OPENAI_API_KEY \
  ghcr.io/OWNER/doctranslater-api:main
```

- With `DOCTRANSLATE_API_AUTH_MODE=disabled` (default), clients need no `Authorization` header.
- With `required`, pass **`Authorization: Bearer $DOCTRANSLATE_API_AUTH_TOKEN`** or **`X-API-Key`** on every protected call (see [HTTP API](http-api.md) for probe exceptions and CORS).

## Local LLM connectivity

Containers cannot reach `localhost` on the host. Point `--local-base-url` (or TOML) at:

- `host.docker.internal` (Docker Desktop; Linux may need `--add-host=host.docker.internal:host-gateway`), or
- Another Compose service name, e.g. `http://ollama:11434`.

See [Local translation](local-translation.md) and [Troubleshooting](troubleshooting.md).

## Troubleshooting

### `ImportError` / missing `.so` in the container

Match the image profile to your flags (OCR → `runtime-vision` or `INCLUDE_OCR=1`). See [Package layers](ai/package-layers.md).

### `Permission denied` on cache or output

Ensure mounted directories are writable by UID **1000**, or run with `--user` matching your volume ownership.

### Warm build fails in CI or offline build hosts

Warm stages need outbound HTTPS (fonts, ONNX, Hugging Face). Use `runtime-*` (non-warm) and run `assets warmup` at deploy time, or ship an offline bundle.

### Hyperscan / glossary errors on `runtime-cpu`

Hyperscan is in the `glossary` extra and needs `libhyperscan5` at runtime. Default `runtime-cpu` does not install that library. Use `runtime-vision` or customize the Dockerfile.

## Related docs

- [Configuration](configuration.md) — CLI flags, TOML, OCR, env vars.
- [Package layers](ai/package-layers.md) — optional extras vs imports.
- [Verification](ai/verification.md) — commands mirrored in CI.
