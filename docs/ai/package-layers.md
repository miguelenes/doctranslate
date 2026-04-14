# Package layers and install profiles

DocTranslater ships as **one PyPI distribution** (`DocTranslater`) with **optional extras** so downstream apps can install only what they need.

## Public import surfaces

| Module | Purpose | Typical extras |
|--------|---------|------------------|
| `doctranslate.schemas` | Pydantic models: router/TOML, `TranslationRequest`, results, events | *none* (base install) |
| `doctranslate.api` | Stable `translate` / `async_translate` / `validate_request` / `inspect_input` / `build_translators` | `full` |
| `doctranslate.http_api` | Optional ASGI app (`create_app`, `serve`); not imported by default CLI | `api` (+ same extras as your translate install) |
| `doctranslate.engine` | Deprecated shim: pipeline entrypoints + `init` — prefer `doctranslate.api` | `full` |
| `doctranslate.pdf` | Deprecated shim: re-exports PDF/IL pipeline — prefer `doctranslate.api` | `full` (or `pdf` + peers) |
| `doctranslate.vision` | Layout model types | `vision` or `full` |
| `doctranslate.experimental` | Unstable experiments — **not** semver | varies |

Deep imports under `doctranslate.format.pdf` remain valid but are **not** semver-guaranteed; prefer `doctranslate.api` for embedding.

## Install matrix (quick)

| Goal | Typical command |
|------|-----------------|
| Types / router TOML models only | `pip install DocTranslater` or `uv sync --locked --group dev` |
| Explicit “schemas” label (same deps as base) | `pip install "DocTranslater[schemas]"` — the `schemas` extra is **intentionally empty** so docs and scripts can request a named slice without adding packages beyond the core dependency set. |
| PDF + CLI, no hosted LLM (combine with `llm` as needed) | `pip install "DocTranslater[pdf,cli,llm]"` |
| Default CLI translate path (matches CI) | `pip install "DocTranslater[full]"` or `uv sync --locked --group dev --extra full` |

Python **3.10–3.13** are supported (`requires-python = ">=3.10,<3.14"` in `pyproject.toml`).

## Optional extras

| Extra | Role |
|-------|------|
| `schemas` | **No extra packages** — reserved alias so install lines can say `DocTranslater[schemas]` when embedding only `doctranslate.schemas` (same as base). |
| `pdf` | PyMuPDF, xsdata/IL, fonts, spatial indexes, scientific helpers |
| `llm` | OpenAI client, httpx, LiteLLM, tiktoken, tenacity |
| `vision` | ONNXRuntime, OpenCV, Hugging Face hub (doclayout assets) |
| `ocr` | RapidOCR ONNX runtime adapter |
| `tm` | SQLite cache / fuzzy TM (peewee, rapidfuzz, Levenshtein) |
| `glossary` | Hyperscan-backed glossary scanning |
| `cli` | Rich, tqdm, psutil (CLI UX); `main.cli()` falls back to stdlib logging if Rich is missing |
| `full` | Meta-extra listing everything needed for the default CLI translate path |
| `api` | FastAPI, Uvicorn, `python-multipart`, `pydantic-settings`, `fsspec` for the optional HTTP service (`doctranslate serve`) |
| `api-s3` | `s3fs`, `boto3` — S3-compatible blob mirror + presigned downloads |
| `api-gcs` | `gcsfs` — GCS blob mirror + signed URLs |
| `tm_semantic` | sentence-transformers + torch (semantic TM tier) |
| `cuda` / `directml` | Alternate ONNXRuntime wheels |

Base dependencies are intentionally small: charset detection, Pydantic, TOML, and `regex` (glossary normalization).

## Which extra do I need?

- **Embed only router/TOML types in another repo:** base install or `pip install "DocTranslater"` and `import doctranslate.schemas`.
- **Run the translate CLI or call `doctranslate.api.translate`:** `pip install "DocTranslater[full]"` (matches CI).
- **Custom subset:** combine extras (for example `pdf`, `llm`, `cli`); resolve import errors by adding the missing slice.

## Import boundaries (OSS)

- `doctranslate.schemas` must not require PyMuPDF, ONNX, or LLM HTTP clients.
- `doctranslate.translator` package `__init__` stays lightweight; heavy symbols load via `__getattr__`.
- CLI subcommands that need the PDF stack import their implementations lazily in `doctranslate/cli/dispatch.py`; cache dirs are created via `doctranslate/bootstrap.py` without importing the full IL graph.

## CI

- **Minimal lane:** `uv sync --locked --group dev` (no extras) + `pytest tests/test_install_profiles.py::test_minimal_schemas_import`.
- **Fast lane:** `uv sync --locked --group dev --extra full` + `pytest tests/ -m "not requires_pdf"` + MkDocs strict + wheel smoke + `scripts/check_cli_import_time.py`.
- **Slim lane:** `uv sync --locked --group dev --extra pdf --extra cli` + `pytest tests/test_install_profiles.py::test_pdf_stack_opens_ci_fixture`.
- **Full matrix:** `uv sync --locked --group dev --extra full` + full `pytest`, assets warmup, offline pack/restore.
- **Docs (PR):** Zensical build when `docs/**` or `mkdocs.yml` changes (`.github/workflows/docs-pr.yml`).

See [Verification](verification.md) for day-to-day commands.

For **OCI images** and which extras each target installs, see [Docker](../docker.md) and [Docker image profiles](../docker-profiles.md).
