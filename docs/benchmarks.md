# Benchmarks and performance

DocTranslater performance depends on **PDF complexity**, **layout model** cost, **LLM latency and pricing**, and **hardware**. The project does **not** publish CI-enforced throughput SLAs; numbers here describe **how to measure** and what to expect at a high level.

## What affects runtime

- **Pages and text volume** — more IL paragraphs mean more LLM round-trips.
- **Router / model** — hosted APIs vs local servers change latency profiles entirely.
- **OCR** — `--ocr-mode` other than `off` adds RapidOCR and image work (optional extra `ocr`).
- **Translation memory** — SQLite and fuzzy tiers add lookup cost but can skip LLM calls.
- **Assets** — first run may download layout models; use `doctranslate assets warmup` and optional offline packs (see [Configuration](configuration.md)).

## Manual end-to-end timing (local LLM)

Use the helper script (requires a **running** local server and a sample PDF):

```bash
uv run python scripts/bench_local_translation.py \
  --pdf examples/ci/test.pdf \
  --lang-in en --lang-out zh \
  --backend ollama --model qwen2.5:7b
```

The script prints JSON with `elapsed_seconds` for the full `translate` subprocess. Compare runs on the same machine only.

## Hosted API runs

For OpenAI or router mode, wall time is dominated by **tokens × model speed × rate limits**. Rough indicative tables for GPT-class models may appear in the root [README](https://github.com/miguelenes/doctranslate/blob/main/README.md#performance-indicative); treat them as **examples**, not guarantees.

## Profiling (contributors)

- **Memray** — optional extra `DocTranslater[memray]`; see [Contributing — Profile memory usage](CONTRIBUTING.md#profile-memory-usage).
- **py-spy** — listed in the dev dependency group for sampling profiles of running processes.

## Automation in CI

The test workflow runs a **warn-only** import/parser timing check so large accidental regressions in CLI startup are visible in logs. It does **not** fail the build on threshold alone (see `scripts/check_cli_import_time.py`).

### Layered harness (micro, meso, HTTP, Docker)

Install perf tooling:

```bash
uv sync --locked --group dev --group perf --extra full
```

| Layer | What | Command / workflow |
|-------|------|-------------------|
| **Micro** | `pytest-benchmark` on parser, mocked router, HTTP inspect, parse-only PDF path | `uv run pytest tests/perf/ -m perf --benchmark-only` (default `pytest tests/` **excludes** `-m perf`; use an explicit `tests/perf/` run) |
| **Meso** | Subprocess CLI timings (help, inspect JSON, `assets warmup`, `translate --skip-translation`) | `uv run python scripts/perf_meso.py` → JSON on stdout |
| **HTTP load** | Locust against a running API | `uv run locust -f benchmarks/load/locustfile.py --headless -u 4 -r 1 -t 20s --host http://127.0.0.1:8999` (set `PERF_INSPECT_PDF` to an absolute path to include `/v1/inspect` in the mix) |
| **Docker** | Image size + `doctranslate --version` in a fresh container + optional API health | `uv run python scripts/perf_docker_metrics.py` (builds `runtime-cpu` / `runtime-api` locally; can take a long time) |
| **Memory** | Memray on short CLI paths | `uv sync --extra memray` then see [Contributing — Profile memory usage](CONTRIBUTING.md#profile-memory-usage); nightly workflow uploads a sample flamegraph when `examples/ci/test.pdf` exists |

**Workflows:** [`.github/workflows/perf-pr.yml`](https://github.com/miguelenes/doctranslate/blob/main/.github/workflows/perf-pr.yml) (path-filtered PR microbenchmarks + JSON artifact), [`.github/workflows/perf-nightly.yml`](https://github.com/miguelenes/doctranslate/blob/main/.github/workflows/perf-nightly.yml) (weekly schedule: microbench, meso JSON, Locust, Memray, Docker metrics with `continue-on-error` where builds may be slow).

**Corpus plan:** [benchmarks/corpus/README.md](https://github.com/miguelenes/doctranslate/blob/main/benchmarks/corpus/README.md) — extend beyond `examples/ci/test.pdf` with licensed fixtures; keep PR jobs small.

**Regression policy:** PR jobs are **informational** (artifacts + logs), not throughput SLAs. To tighten later, use `pytest-benchmark`’s `--benchmark-compare-fail` only after collecting a stable baseline on one OS/Python tuple.

### Runtime metrics (operators)

When the HTTP API runs with Prometheus enabled, histograms such as `doctranslate_pipeline_stage_duration_seconds`, `doctranslate_translator_latency_seconds`, and `doctranslate_job_duration_seconds` complement microbenchmarks for deployment-level drift; see [Observability](observability.md).
