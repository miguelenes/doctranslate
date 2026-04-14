# DocTranslate

**A powerful, extensible document translation engine with multi-translator orchestration and advanced PDF handling.**

> **Note:** This is a customized fork of [DocTranslate](https://github.com/funstory-ai/DocTranslate) by funstory-ai. It builds upon DocTranslate's core translation pipeline and adds new architectural features. See [Attribution](#attribution) below for details.

---

## 🎯 Overview

DocTranslate is a specialized document translation system designed for **high-quality, accurate translation of complex PDFs** with preservation of layout, formatting, and visual elements.

### Key Features

- **Multi-Translator Backend Routing**: Automatically failover between OpenAI, Anthropic, local LLMs, and more
- **Smart Document Analysis**: YOLO-based layout detection for figures, tables, formulas, and text regions
- **Advanced PDF Handling**: Pixel-perfect text positioning, font subsetting, watermarking, dual-language output
- **Glossary System**: Automatic term extraction and custom glossary management
- **Parallel Processing**: Split large documents and process pages in parallel
- **Cost Optimization**: Track per-translator costs and route to cheapest available backend
- **Extensible Architecture**: Easy to add custom translators, post-processors, and quality scorers

### Typical Use Cases

- Technical documentation (whitepapers, research papers, academic PDFs)
- Regulatory documents (contracts, compliance reports)
- Marketing materials (brochures, datasheets)
- Multilingual project management (translating to 50+ languages)

---

## 🚀 Installation

### Requirements
- Python 3.10+
- pip or conda

### Quick Start

```bash
# Clone and install
git clone https://github.com/miguelenes/doctranslate.git
cd doctranslate
pip install -e .

# Verify installation
doctranslate --version
doctranslate --help
```

---

## 📖 Usage

### Basic translation (legacy OpenAI path)

```bash
export OPENAI_API_KEY=sk-...

doctranslate --openai \
  --files input.pdf \
  --lang-in en --lang-out zh \
  --output output_zh.pdf
```

Use `--openai-model`, `--openai-base-url`, and optional `--openai-term-extraction-*` flags as documented in `doctranslate --help`. With the default OpenAI API host, the legacy path may use the **Responses** API for simple `translate()` calls and **structured parse** for JSON-heavy `llm_translate()` flows (term extraction, batched IL translation); custom `--openai-base-url` gateways use chat completions only.

### Multi-provider router (TOML)

```bash
doctranslate --translator router \
  --config doctranslate.toml \
  --files input.pdf \
  --lang-in en --lang-out es \
  --output output.pdf
```

### Local translation (Ollama, vLLM, llama.cpp server)

No hosted API key required. Example with [Ollama](https://ollama.com/):

```bash
doctranslate --translator local \
  --local-backend ollama \
  --local-model qwen2.5:7b \
  --files input.pdf --lang-in en --lang-out zh \
  --output output.pdf
```

See **[Local translation](docs/local-translation.md)** for vLLM / OpenAI-compatible URLs, TOML options, batch tuning, and troubleshooting.

**Example `doctranslate.toml`** (nested providers + profiles; secrets via env):

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

Validate configuration without running a job:

```bash
doctranslate --translator router --config doctranslate.toml --validate-translators
```

### Programmatic setup

Use `doctranslate.translator.factory.build_translators` with `translator_mode="router"` and a config path, or construct `TranslatorRouter` with `LiteLLMProviderExecutor` instances for advanced/testing scenarios (see `tests/test_translator_router.py`).

---

## 🏗️ Architecture

DocTranslate uses a multi-stage **Intermediate Language (IL)** compilation pipeline:

```
PDF Input
    ↓
[Frontend] ILCreater         → Parse PDF structure
    ↓
[Midend]  LayoutParser       → Detect layout regions (YOLO)
          ParagraphFinder    → Group characters into paragraphs
          ILTranslator       → Translate via LLM (multi-translator router)
          Typesetting        → Re-flow text into page geometry
    ↓
[Backend] PDFCreater         → Render IL to PDF
    ↓
PDF Output (single/dual-language, watermarked)
```

### Multi-provider routing

**`TranslatorRouter`** (`doctranslate/translator/router.py`) — sync, `BaseTranslator`-compatible:

- LiteLLM-backed providers: OpenAI, Anthropic, OpenRouter, OpenAI-compatible gateways, Ollama
- Strategies: `failover`, `round_robin`, `least_loaded`, `cost_aware`
- Per-provider metrics (requests, latency, tokens, estimated cost) and optional JSON export

---

## 📚 Documentation

- **[Getting Started](docs/index.md)** — Installation and first steps
- **[Configuration Guide](docs/configuration.md)** — All command-line options and config file format
- **[Multi-Translator Setup](docs/multi-translator.md)** — Using the router with multiple backends
- **[Supported Languages](docs/supported_languages.md)** — Full list of supported language pairs
- **[Implementation Details](docs/ImplementationDetails/)** — Deep dives into each pipeline stage
- **[Contributing](docs/CONTRIBUTING.md)** — How to contribute improvements

---

## 🔧 Development

### Setting Up Development Environment

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/doctranslate.git
cd doctranslate

# Create virtual environment
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate

# Install project + dev dependencies (pytest, ruff, …)
uv sync --group dev

# Run tests
uv run pytest tests/ -v

# Build docs
mkdocs serve  # http://localhost:8000
```

### Running Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_translator_router.py -v

# With coverage
pytest --cov=doctranslate tests/
```

---

## 📄 Attribution

**DocTranslate** is a customized fork of **[DocTranslate](https://github.com/funstory-ai/DocTranslate)** by **funstory-ai Limited**, licensed under AGPL-3.0.

### What's the Same (from DocTranslate)
- Core IL (Intermediate Language) pipeline
- Document layout detection (YOLO-based)
- PDF parsing and rendering utilities
- Glossary system
- Translation caching

### What's New (in DocTranslate)
- **Multi-Translator Router**: Flexible orchestration across multiple LLM backends
- **Rebranding**: New user-facing CLI, package name, and documentation
- **Architecture Improvements**: Enhanced configuration, better extensibility

### License Compliance
Both DocTranslate and DocTranslate are licensed under **GNU Affero General Public License v3.0 (AGPL-3.0)**.

If you run DocTranslate as a service, you must provide source code to users (AGPL §13). See `LICENSE` and `LICENSE.ADDITIONS` for full terms.

---

## 📈 Performance

Benchmarks on typical PDF documents (tested with GPT-4):

| Document Type | Pages | Time (minutes) | Cost |
|---------------|-------|----------------|------|
| Technical whitepaper | 15 | 3.5 | $0.45 |
| Research paper | 25 | 6.2 | $0.78 |
| Regulatory doc | 50 | 12.1 | $1.52 |

*Times include layout detection, translation, and PDF rendering. Actual costs depend on translator backend and token usage.*

---

## 🐛 Troubleshooting

### Common Issues

**Q: "No module named 'doctranslate'"**
```bash
# Ensure installation completed
pip install -e .

# Check import
python -c "import doctranslate; print(doctranslate.__version__)"
```

**Q: Translation is slow**
- Use the router with `least_loaded` or `cost_aware` strategy where appropriate
- Enable parallel processing with `--split-pages N`
- Consider switching to faster (but possibly lower-quality) LLM backend

**Q: PDF layout is broken after translation**
- Check that `--font-fallback` is set correctly
- Try disabling `--watermark` to rule out watermark overlap issues
- Verify source PDF is not a scanned image

### Getting Help

- Check `docs/CONTRIBUTING.md` for guidelines
- Open an issue on GitHub
- Review existing issues for solutions

---

## 📊 Metrics & monitoring

After a run with `--translator router`, the CLI logs per-provider metrics when `metrics_output` includes `log`. In code, a `TranslatorRouter` exposes:

```python
for pid, stats in router.get_metrics().items():
    print(pid, stats.success_rate, stats.total_cost_usd, stats.avg_latency_ms)
print(router.print_metrics())
```

See [docs/multi-translator.md](docs/multi-translator.md) for JSON export options.

---

## 📝 License

DocTranslate is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

- You can use, modify, and distribute this software
- If you modify it, you must share your modifications under AGPL-3.0
- If you run this as a service, you must provide source to users
- The original DocTranslate copyright notice must be preserved

See `LICENSE` and `LICENSE.ADDITIONS` for full details.

---

## 🙏 Credits

**Original Project:** [DocTranslate](https://github.com/funstory-ai/DocTranslate) by **funstory-ai Limited**

**Customized By:** Miguel Enes (2025)

---

**Questions?** Open an issue or check the [documentation](docs/).
# doctranslate
