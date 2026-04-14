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
