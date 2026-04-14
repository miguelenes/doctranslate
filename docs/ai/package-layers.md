# Package layers and install profiles

DocTranslater ships as **one PyPI distribution** (`DocTranslater`) with **optional extras** so downstream apps can install only what they need.

## Public import surfaces

| Module | Purpose | Typical extras |
|--------|---------|------------------|
| `doctranslate.schemas` | Pydantic/TOML config types and translation settings | *none* (base install) |
| `doctranslate.api` | Stable `translate` / `async_translate` / `build_translators` | `full` |
| `doctranslate.engine` | Same engine entrypoints + `init` | `full` |
| `doctranslate.pdf` | Re-exports PDF/IL pipeline | `full` (or `pdf` + peers) |
| `doctranslate.vision` | Layout model types | `vision` or `full` |

Deep imports under `doctranslate.format.pdf` remain valid but are **not** semver-guaranteed; prefer `doctranslate.api` for embedding.

## Optional extras

| Extra | Role |
|-------|------|
| `pdf` | PyMuPDF, xsdata/IL, fonts, spatial indexes, scientific helpers |
| `llm` | OpenAI client, httpx, LiteLLM, tiktoken, tenacity |
| `vision` | ONNXRuntime, OpenCV, Hugging Face hub (doclayout assets) |
| `ocr` | RapidOCR ONNX runtime adapter |
| `tm` | SQLite cache / fuzzy TM (peewee, rapidfuzz, Levenshtein) |
| `glossary` | Hyperscan-backed glossary scanning |
| `cli` | Rich, tqdm, psutil (CLI UX); `main.cli()` falls back to stdlib logging if Rich is missing |
| `full` | Meta-extra listing everything needed for the default CLI translate path |
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
- **Full lane:** `uv sync --locked --group dev --extra full` + full `pytest`, MkDocs strict, assets warmup.

See [Verification](verification.md) for day-to-day commands.
