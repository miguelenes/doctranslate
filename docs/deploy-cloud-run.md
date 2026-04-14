# Deploy on Google Cloud Run

This guide deploys the **`runtime-api`** image (HTTP API on port **8000**) as the primary OSS reference for serverless containers. For background and other platforms, see [Serverless containers](serverless-containers.md).

## Prerequisites

- Google Cloud project with **Artifact Registry** or **Container Registry**, and **Cloud Run API** enabled.
- A built image: use [prebuilt GHCR images](docker.md#prebuilt-images-github-container-registry) or `docker build --target runtime-api -t REGION-docker.pkg.dev/PROJECT/REPO/doctranslate-api:TAG .`

## Quick deploy (`gcloud`)

Replace placeholders (`PROJECT`, `REGION`, `IMAGE`).

```bash
gcloud run deploy doctranslater-api \
  --project=PROJECT \
  --region=REGION \
  --image=IMAGE \
  --port=8000 \
  --cpu=2 \
  --memory=4Gi \
  --min-instances=0 \
  --max-instances=10 \
  --timeout=3600 \
  --session-affinity \
  --set-env-vars=DOCTRANSLATE_API_MAX_CONCURRENT_JOBS=1
```

Notes:

- **`--port=8000`** must match the container listen port (`Dockerfile` `CMD` for `runtime-api`).
- **`--timeout`**: maximum **request** time (including long-running HTTP connections if your client holds the connection open). For very large PDFs, prefer a **worker** pattern ([Serverless containers](serverless-containers.md)) or raise timeout within [Cloud Run limits](https://cloud.google.com/run/docs/configuring/request-timeout).
- **`--session-affinity`**: helps clients stick to one revision instance while polling **in-process** jobs (`202` + `GET /v1/jobs/{id}`). It is **not** a substitute for an external job store at high scale—see [HTTP API – Serverless and multi-instance behavior](http-api.md#serverless-and-multi-instance-behavior).
- **Secrets**: pass LLM keys with **`--set-secrets=OPENAI_API_KEY=openai-api-key:latest`** (after creating the secret) or Secret Manager volume mounts; do not bake keys into images ([Docker – Security](docker.md#security)).

## Environment variables (Cloud Run)

Set the same variables as in [HTTP API – Environment variables](http-api.md#environment-variables). Common Cloud Run additions:

| Variable | Recommendation |
|----------|----------------|
| `DOCTRANSLATE_API_DATA_ROOT` | `/tmp/doctranslate-api` or a mounted volume path if using [Cloud Run volumes](https://cloud.google.com/run/docs/configuring/services/cloud-storage-volume-mounts) |
| `DOCTRANSLATE_API_TMP_ROOT` | Optional; defaults under `data_root/tmp` |
| `DOCTRANSLATE_API_WARMUP_ON_STARTUP` | `eager` to reduce first-request latency (downloads/fonts/models; slower startup) |
| `DOCTRANSLATE_API_REQUIRE_ASSETS_READY` | `true` if `/v1/health/ready` must block until assets exist |
| `DOCTRANSLATE_API_JOB_TIMEOUT_SECONDS` | Set to bound wall-clock per job (e.g. `7200`) |

Mount a volume (or use an init sidecar pattern) for **`/home/doctranslater/.cache/doctranslate`** if you want persistent ONNX/font caches across instances.

## Health checks

- **Liveness**: `GET /v1/health/live`
- **Readiness**: `GET /v1/health/ready` (writable dirs, optional assets, job capacity)

Configure Cloud Run startup probe / health checks to hit **`/v1/health/ready`** when using `DOCTRANSLATE_API_REQUIRE_ASSETS_READY=true` or after warm-up.

## Example manifest (Knative / Cloud Run YAML)

A minimal **Knative Service** shape (exact schema depends on your Cloud Run / Anthos setup):

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: doctranslater-api
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "0"
        autoscaling.knative.dev/maxScale: "10"
    spec:
      containerConcurrency: 8
      timeoutSeconds: 3600
      containers:
        - image: ghcr.io/OWNER/doctranslater-api:main
          ports:
            - containerPort: 8000
          env:
            - name: DOCTRANSLATE_API_MAX_CONCURRENT_JOBS
              value: "1"
```

Repository copy: [`docs/deploy-samples/cloud-run-service.sample.yaml`](deploy-samples/cloud-run-service.sample.yaml).

## Cold start and cost

- **Min instances > 0** reduces cold latency for interactive use.
- **Warm images** (`runtime-api` built from warm builder stages) are not published by default CI; either build a custom warm image or run `POST /v1/assets/warmup` after deploy.

## Verify

```bash
curl -sS "https://YOUR-SERVICE-URL/v1/health/live"
curl -sS "https://YOUR-SERVICE-URL/v1/health/ready"
```

Smoke a **no-LLM** pipeline check using `skip_translation` (see [HTTP API – Docker](http-api.md#docker)) once `OPENAI_API_KEY` is set (translator is still constructed; use a placeholder only for this smoke if your policy allows).

## Related

- [Serverless runtime & image reference](serverless-runtime-reference.md)
- [Docker](docker.md) · [HTTP API](http-api.md)
