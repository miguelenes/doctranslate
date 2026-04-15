# Observability

DocTranslater exposes **structured logs**, optional **Prometheus** metrics, and optional **OpenTelemetry** tracing across the CLI, HTTP API, ARQ workers, PDF pipeline, and translator routing.

## Profiles and environment

Settings are read from process environment variables (shared by `doctranslate serve`, `doctranslate worker`, and CLI translate runs).

| Variable | Default | Meaning |
|----------|---------|---------|
| `DOCTRANSLATE_OBS_PROFILE` | `minimal` | `minimal` \| `logs_only` \| `prometheus` \| `otlp` (OTLP enables tracing export) |
| `DOCTRANSLATE_LOG_FORMAT` | `json` | `json` or `console` (human-friendly) |
| `DOCTRANSLATE_LOG_LEVEL` | `INFO` | Root log level |
| `DOCTRANSLATE_LOG_REDACT_USER_TEXT` | `true` | Truncate/redact sensitive-looking log payloads |
| `DOCTRANSLATE_REQUEST_ID_HEADER` | `X-Request-ID` | Incoming correlation header; response echoes the resolved id |
| `DOCTRANSLATE_METRICS_ENABLED` | `true` | When `false`, Prometheus instruments are not registered |
| `DOCTRANSLATE_METRICS_PATH` | `/metrics` | Path for the Prometheus scrape endpoint (HTTP API only) |
| `DOCTRANSLATE_METRICS_NAMESPACE` | `doctranslate` | Metric name prefix |
| `DOCTRANSLATE_OTEL_ENABLED` | `false` | Set `true` or use profile `otlp` to configure tracing |
| `DOCTRANSLATE_OTEL_SERVICE_NAME` | `doctranslate` | `service.name` resource attribute |
| `DOCTRANSLATE_OTEL_RESOURCE_ATTRIBUTES` | *(empty)* | Comma-separated `key=value` pairs merged into the resource |

Standard **OTLP exporter** environment variables (for example `OTEL_EXPORTER_OTLP_ENDPOINT`) are honored by the SDK when tracing is enabled.

## HTTP API

- **Request IDs:** Every response includes `X-Request-ID`. Error bodies (`ApiErrorEnvelope`) include the same `request_id` for log correlation.
- **Prometheus:** `GET /metrics` exposes RED-style HTTP metrics, job queue depth (updated on readiness checks), job lifecycle histograms, pipeline stage timings (when the PDF stack runs), translator router counters, and asset warmup counters when metrics are enabled. These histograms are the primary **runtime** regression signals in production (complement OSS microbenchmarks in [Benchmarks](benchmarks.md)).
- **Tracing:** With `DOCTRANSLATE_OTEL_ENABLED=true` and a reachable OTLP collector, spans cover FastAPI requests (via auto-instrumentation), ARQ job execution (`job.execute`, `job.warmup`), and PDF `pipeline.translate_sync`. For **split API + worker** deployments, the API stores a W3C `traceparent` on queued jobs so the worker can continue the trace.

## Workers (ARQ)

Run the worker with the same `DOCTRANSLATE_*` observability variables as the API. Metrics use the same registry naming; scrape **each process** that should be monitored (API and workers are separate processes).

## CLI

`doctranslate translate` configures structured logging and optional Prometheus metrics using the same environment variables. Each CLI invocation binds a fresh `cli_run_id` in log context.

## Router metrics vs service metrics

TOML/CLI **`metrics_output`** / **`metrics_json_path`** still control end-of-run **router summaries** (per-provider tokens, cost, latency averages). Service-level Prometheus metrics complement those with labeled counters/histograms suitable for dashboards.

## Docker and serverless

- Default **OSS / Docker** profile: JSON logs + `/metrics` on the API container.
- Ship **stdout/stderr** to your platform log sink; correlate with **`job_id`** and **`X-Request-ID`**.
- For multi-replica setups, see [HTTP API](http-api.md) queue modes and [HTTP API workers](http-api-workers.md).

## Security

- Logs apply **redaction** for common secret keys and long strings when `DOCTRANSLATE_LOG_REDACT_USER_TEXT` is true.
- Do not enable verbose logging of raw document text in production.

## Phased rollout (contributors)

Suggested PR sequence to keep risk bounded:

1. **Foundation** — `doctranslate.observability` package, settings, structured logging, request-id middleware.
2. **HTTP metrics** — `/metrics`, HTTP + job queue gauges, error envelope correlation.
3. **Worker tracing** — persist `traceparent`, `job.execute` / warmup spans, terminal job metrics.
4. **Translator** — router Prometheus instruments while preserving `metrics_output` / `metrics_json_path`.
5. **PDF stages** — `ProgressMonitor` stage timings and pipeline spans.
6. **Docs/tests** — expand coverage and deployment guides (this page, HTTP API, Docker/serverless).
