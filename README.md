# DocTranslater

Translate **PDFs** while keeping layout, figures, and structure as intact as possible. DocTranslater turns pages into an intermediate representation, sends text to your chosen LLM backend, then typesets the result back into a new PDF.

**This repo:** [miguelenes/doctranslate](https://github.com/miguelenes/doctranslate) — a maintained fork of [funstory-ai/DocTranslate](https://github.com/funstory-ai/DocTranslate). Fork lineage and license notes live under [Attribution](#attribution) at the end of this file so they do not slow you down.

---

## Where to go next

Pick what you need — you can always come back here.

| I want to… | Start here |
|------------|------------|
| Install and run my first translation | [Start here (~5 minutes)](#start-here-5-minutes) |
| Run in Docker (Linux images) | [Docker](docs/docker.md) |
| Pull prebuilt images (GHCR) | [Docker — Prebuilt images](docs/docker.md#prebuilt-images-github-container-registry) |
| See every CLI flag and config option | [Configuration](docs/configuration.md) |
| Use several providers (failover, cost-aware routing) | [Multi-translator setup](docs/multi-translator.md) |
| Run without a hosted API (Ollama, vLLM, …) | [Local translation](docs/local-translation.md) |
| Browse the full docs site | [Getting started](docs/index.md) |
| Contribute code or report issues | [Contributing](docs/CONTRIBUTING.md) |
| Dig into pipeline stages | [Implementation details](docs/ImplementationDetails/) |

---

## Start here (~5 minutes)

You will: clone the project, install dependencies, and produce one translated PDF (using OpenAI as the simplest hosted path).

**Requirements:** Python 3.10+ and [uv](https://docs.astral.sh/uv/) (recommended).

**PyPI / library installs:** use the `full` extra so all PDF, LLM, OCR, TM, and CLI pieces resolve (`pip install "DocTranslater[full]"`). A smaller **schemas-only** footprint is documented in [docs/ai/package-layers.md](docs/ai/package-layers.md).

```bash
git clone https://github.com/miguelenes/doctranslate.git
cd doctranslate
uv sync --locked --group dev --extra full

uv run doctranslate --version
uv run doctranslate --help
# Same CLI, alternate entry point:
uv run doc-translate --help
```

Set your API key and translate a file (replace paths and languages as needed). The CLI uses **subcommands** (for example `translate`, `assets`). See [docs/migration.md](docs/migration.md) if you are upgrading from 0.5.x.

```bash
export OPENAI_API_KEY="sk-..."

uv run doctranslate translate input.pdf \
  --provider openai \
  --source-lang en --target-lang zh \
  -o ./out
```

**When it works:** you should see new PDFs under the output **directory** (`-o` / `--output-dir`). If something fails, check [Troubleshooting](#troubleshooting) below or run `uv run doctranslate --help` / `uv run doctranslate translate --help`.

**Scanned or messy PDFs?** Try OCR before layout (still PDF → IL → LLM → PDF):

```bash
uv run doctranslate translate scan.pdf --provider openai \
  --source-lang en --target-lang zh --ocr-mode auto
```

Details: [Configuration](docs/configuration.md) (`--ocr-mode`, `--ocr-pages`, `--ocr-debug`).

---

## What you get

DocTranslater is aimed at **technical and layout-heavy PDFs**: papers, manuals, specs, and reports where you care about paragraphs, tables, and figures staying readable.

**Highlights**

- **Several backends:** route across OpenAI, Anthropic, local models, and more (router mode).
- **Layout-aware processing:** YOLO-based regions for figures, tables, formulas, and body text.
- **Strong PDF output:** reflow into page geometry, font handling, optional watermarking, single- or dual-language PDFs.
- **Glossaries:** term extraction and custom glossary workflows.
- **Scale:** split large jobs and process pages in parallel when it helps.
- **Cost and reliability:** per-provider metrics and strategies like failover or cost-aware routing.
- **Translation memory (optional):** reuse prior segments — [docs/translation-memory.md](docs/translation-memory.md).

**Typical uses:** research PDFs, compliance packs, datasheets, internal docs, anything where “plain text dump” is not enough.

---

## Usage (pick your path)

The sections below assume you already ran `uv sync --locked --group dev --extra full` and use `uv run doctranslate …`. If you installed the package into an active environment, you can call `doctranslate` directly instead.

### OpenAI (quick path)

```bash
export OPENAI_API_KEY="sk-..."

uv run doctranslate translate input.pdf \
  --provider openai \
  --source-lang en --target-lang zh \
  -o ./out
```

Warm assets / offline bundle:

```bash
uv run doctranslate assets warmup
uv run doctranslate assets pack-offline /path/to/bundle_dir
uv run doctranslate assets restore-offline /path/to/bundle.tar.zst
```

Use `--openai-model`, `--openai-base-url`, and optional `--openai-term-extraction-*` (see `doctranslate translate --help`).

**API behavior note:** on the default OpenAI host, simple `translate()` calls may use the **Responses** API, while JSON-heavy `llm_translate()` flows (term extraction, batched IL translation) may use **structured parse**. If you set a custom `--openai-base-url` gateway, chat completions are used throughout.

### Multi-provider router (TOML)

Best when you want **profiles**, **failover**, or **mixing providers**. Point the CLI at a config file:

```bash
uv run doctranslate translate input.pdf \
  --provider router \
  -c doctranslate.toml \
  --source-lang en --target-lang es \
  -o ./out
```

**Example `doctranslate.toml`** (nested providers + profiles; secrets via environment variables):

```toml
[doctranslate]
translator = "router"
routing_profile = "translate"
term_extraction_profile = "terms"
routing_strategy = "failover"
metrics_output = "log"

[doctranslate.profiles.translate]
providers = ["openai_fast", "anthropic_backup"]
strategy = "failover"
max_attempts = 4
require_json_mode = false

[doctranslate.profiles.terms]
providers = ["openai_fast"]
strategy = "failover"
require_json_mode = true

[doctranslate.providers.openai_fast]
provider = "openai"
model = "gpt-4o-mini"
api_key_env = "OPENAI_API_KEY"

[doctranslate.providers.anthropic_backup]
provider = "anthropic"
model = "claude-3-5-sonnet-latest"
api_key_env = "ANTHROPIC_API_KEY"
```

Validate configuration without running a full job:

```bash
uv run doctranslate config validate --translator router -c doctranslate.toml
```

More examples and JSON metrics export: [docs/multi-translator.md](docs/multi-translator.md).

### Local translation (no hosted API key)

Example with [Ollama](https://ollama.com/):

```bash
uv run doctranslate translate input.pdf \
  --provider local \
  --local-backend ollama \
  --local-model qwen2.5:7b \
  --source-lang en --target-lang zh \
  -o ./out
```

vLLM, OpenAI-compatible URLs, batch tuning, and troubleshooting: **[Local translation](docs/local-translation.md)**.

### Using DocTranslater from Python

Use the stable API: **`doctranslate.api`** with `TranslationRequest` / `TranslationResult`, or `doctranslate.schemas` for Pydantic models only. See **[Stable library API](docs/library-api.md)** and **[Public API policy](docs/public-api-policy.md)**.

For router mode, set `translator.mode` to `router` in the request (or call `doctranslate.api.build_translators` with `translator_mode="router"` when you need `TranslatorRouter` instances for metrics or tests — see `tests/test_translator_router.py`).

---

## Architecture (short version)

DocTranslater is a **PDF → intermediate language (IL) → LLM → PDF** pipeline. In plain terms: it understands page structure, translates text in context, then lays translated text back onto the page instead of pasting a single blob of text.

```
PDF Input
    ↓
[Frontend] ILCreater         → Parse PDF structure
    ↓
[Midend]  LayoutParser       → Detect layout regions (YOLO)
          ParagraphFinder    → Group characters into paragraphs
          ILTranslator         → Translate via LLM (incl. multi-translator router)
          Typesetting          → Reflow text into page geometry
    ↓
[Backend] PDFCreater         → Render IL to PDF
    ↓
PDF Output (single/dual-language, watermarked)
```

### Multi-provider routing

**`TranslatorRouter`** (`doctranslate/translator/router.py`) — synchronous and `BaseTranslator`-compatible:

- LiteLLM-backed providers: OpenAI, Anthropic, OpenRouter, OpenAI-compatible gateways, Ollama
- Strategies: `failover`, `round_robin`, `least_loaded`, `cost_aware`
- Per-provider metrics (requests, latency, tokens, estimated cost) and optional JSON export

---

## Metrics and monitoring

After a run with `--translator router`, the CLI logs per-provider metrics when `metrics_output` includes `log`. In application code, a `TranslatorRouter` exposes metrics you can record with `logging` (avoid `print()` in libraries and tools — see [Contributing](docs/CONTRIBUTING.md)):

```python
import logging

log = logging.getLogger(__name__)

for pid, stats in router.get_metrics().items():
    log.debug(
        "%s success=%.3f cost_usd=%.4f avg_latency_ms=%.1f",
        pid,
        stats.success_rate,
        stats.total_cost_usd,
        stats.avg_latency_ms,
    )
log.debug("%s", router.print_metrics())
```

JSON export and router options: [docs/multi-translator.md](docs/multi-translator.md).

---

## Development

```bash
git clone https://github.com/miguelenes/doctranslate.git
cd doctranslate

# Optional: classic venv (uv still manages deps below)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

uv sync --locked --group dev --extra full
uv run pytest tests/ -v

# Docs: live preview
uv run mkdocs serve   # http://127.0.0.1:8000

# Same static output as CI
uv run zensical build --clean
```

GitHub Pages publishing on push to `main` is described in [docs/github-pages.md](docs/github-pages.md).

**Focused tests**

```bash
uv run pytest tests/ -q
uv run pytest tests/test_translator_router.py -v
uv run pytest --cov=doctranslate tests/
```

---

## Performance (indicative)

Rough **order-of-magnitude** figures on typical PDFs (hosted GPT-class models; your mileage will vary). These are **not** CI-enforced SLAs — for methodology, local timing, and automation limits see [docs/benchmarks.md](docs/benchmarks.md).

| Document type        | Pages | Time (minutes) | Cost (USD) |
|----------------------|-------|----------------|------------|
| Technical whitepaper | 15    | 3.5            | 0.45       |
| Research paper       | 25    | 6.2            | 0.78       |
| Regulatory doc       | 50    | 12.1           | 1.52       |

Times include layout detection, translation, and PDF rendering. Actual cost depends on backend, model, and token usage.

---

## Troubleshooting

Short answers below; the full guide is [docs/troubleshooting.md](docs/troubleshooting.md).

**`No module named 'doctranslate'`**

```bash
uv sync --locked --group dev --extra full
uv run python -c "import doctranslate; print(doctranslate.__version__)"
```

If you use pip in an editable install: `pip install -e .`

**Translation is slow**

- Router: try `least_loaded` or `cost_aware` where appropriate.
- Enable split translation with `doctranslate translate … --split-pages N` (alias `--max-pages-per-part`).
- Use a faster (sometimes lower-quality) model for drafts.

**Layout looks wrong after translation**

- Tune fonts with `--primary-font-family` (see `doctranslate translate --help`).
- Try `--watermark-mode no_watermark` (alias `--watermark-output-mode`).
- Confirm the source is not an image-only scan without OCR — see `--ocr-mode` above.

**Getting help**

- Guidelines: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- [Open an issue](https://github.com/miguelenes/doctranslate/issues) or search existing ones

---

## Documentation index

- [Getting started](docs/index.md) — install and first steps
- [Configuration](docs/configuration.md) — CLI and config file
- [Multi-translator setup](docs/multi-translator.md) — router and providers
- [Supported languages](docs/supported_languages.md)
- [Implementation details](docs/ImplementationDetails/) — pipeline deep dives
- [Contributing](docs/CONTRIBUTING.md)

---

## Attribution

**DocTranslater** (this fork) builds on **[DocTranslate](https://github.com/funstory-ai/DocTranslate)** by **funstory-ai Limited**, under **AGPL-3.0**.

**Shared with upstream**

- Core IL pipeline
- YOLO-based layout detection
- PDF parsing and rendering utilities
- Glossary system and translation caching

**Notable additions in this fork**

- Multi-translator router and richer configuration
- Rebranded CLI, package layout, and documentation refresh
- General architecture and extensibility improvements

**License compliance:** this fork and upstream are **GNU Affero General Public License v3.0 (AGPL-3.0)**. If you run DocTranslater as a service, you must offer corresponding source to users (AGPL §13). Full text: `LICENSE` and `LICENSE.ADDITIONS`.

---

## License

DocTranslater is licensed under **GNU Affero General Public License v3.0 (AGPL-3.0)**.

- You may use, modify, and distribute this software under the license terms.
- Modifications must remain under AGPL-3.0.
- Network use as a service triggers source-offer obligations — read `LICENSE`.
- Preserve upstream copyright notices as required.

---

## Credits

- **Original project:** [DocTranslate](https://github.com/funstory-ai/DocTranslate) — funstory-ai Limited  
- **This fork:** Miguel Enes (2025)

---

**Questions?** Open an [issue](https://github.com/miguelenes/doctranslate/issues) or browse the [docs/](docs/) folder.
