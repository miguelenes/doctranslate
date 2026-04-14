# Deploy on AWS ECS Fargate and App Runner

This page covers **AWS ECS Fargate** (strong fit for workers and long jobs) and **AWS App Runner** (simpler HTTP service, with caveats). See [Serverless containers](serverless-containers.md) for the full platform matrix.

## ECS Fargate

### Service vs worker

| Pattern | Image | Entry command | When to use |
|---------|-------|---------------|-------------|
| **HTTP service** | `runtime-api` | Default `doctranslate serve --host 0.0.0.0 --port 8000` | API + in-process jobs behind ALB |
| **Worker** | `runtime-cpu` or `runtime-vision` | `doctranslate translate …` or your wrapper | SQS / Step Functions / EventBridge driven batch |

### Task definition hints

- **Port**: container port **8000** for `runtime-api`.
- **CPU / memory**: start at **2 vCPU / 4 GB** for API; **4 vCPU / 8 GB** for heavy OCR / large PDFs (`runtime-vision`).
- **Ephemeral storage**: default 20 GiB may be tight for large jobs; increase **ephemeralStorage** in the task definition when needed.
- **Read-only root**: if `readonlyRootFilesystem=true`, mount writable volumes for `DOCTRANSLATE_API_DATA_ROOT`, `DOCTRANSLATE_API_TMP_ROOT`, and `HOME/.cache/doctranslate`.
- **EFS**: optional mount for persistent font/model cache across tasks.

### Load balancer + session affinity

For `runtime-api`, place an **Application Load Balancer** target group in front of the service. Enable **sticky sessions** (target group stickiness) if clients poll job status on the same host—same caveat as Cloud Run: stickiness is best-effort; production multi-replica setups should use an **external queue + object storage** ([HTTP API](http-api.md#serverless-and-multi-instance-behavior)).

### Autoscaling

Use **ECS Service Auto Scaling** on CPU, memory, or custom metrics (e.g. SQS queue depth for workers). Cap **`DOCTRANSLATE_API_MAX_CONCURRENT_JOBS`** per task so scaling adds capacity instead of OOMs.

### Example snippets

Repository samples (adjust ARNs, subnets, security groups):

- [`docs/deploy-samples/ecs-taskdef-api.sample.yaml`](deploy-samples/ecs-taskdef-api.sample.yaml) — Fargate task definition skeleton for `runtime-api`.

## AWS App Runner

App Runner is a **managed HTTP service** with less control than Fargate.

- **Fit**: light traffic, smaller PDFs, or **control-plane** endpoints (`/v1/inspect`, `/v1/config/validate`) if you offload translation to Fargate workers.
- **Caveats**:
  - **Request timeouts** and **concurrency** models differ from raw Fargate; very long translations may still need a worker pattern.
  - **Sticky routing** is not as explicit as ALB stickiness—treat multi-instance job polling as **non-portable** without external state.

Configure **port 8000**, health check HTTP path **`/v1/health/ready`** (or `/v1/health/live` for liveness-only), and pass the same env vars as [HTTP API](http-api.md#environment-variables).

## Artifact and state

- Use **S3** for durable inputs/outputs; task disk for scratch only.
- Set `DOCTRANSLATE_API_DATA_ROOT` to a writable path on the task volume.

## Related

- [Deploy on Cloud Run](deploy-cloud-run.md) (primary reference)
- [Modal and Runpod notes](deploy-modal-runpod.md)
- [Serverless runtime & image reference](serverless-runtime-reference.md)
