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
git clone https://github.com/YOUR_USERNAME/doctranslate.git
cd doctranslate
pip install -e .

# Verify installation
doctranslate --version
doctranslate --help
```

---

## 📖 Usage

### Basic Translation

```bash
# Translate a PDF to Chinese
doctranslate input.pdf \
  --output-language zh \
  --api-key sk-... \
  --output output_zh.pdf
```

### Multi-Translator with Failover

```bash
# Use configuration file for multiple translators
doctranslate input.pdf \
  --config doctranslate.toml \
  --output output.pdf
```

**doctranslate.toml:**
```toml
[doctranslate]
output_language = "es"
output_file = "output.pdf"
translator = "router"  # Use multi-translator router

# Primary: OpenAI (fast, expensive)
openai_api_key = "sk-..."

# Fallback: Anthropic (slower, cheaper)
anthropic_api_key = "sk-ant-..."
```

### Advanced: Custom Routing Strategy

```python
from doctranslate.translator.router import TranslatorRouter, RouterStrategy
from doctranslate.translator import OpenAITranslator, AnthropicTranslator

# Create router with multiple backends
router = TranslatorRouter([
    OpenAITranslator(model="gpt-4", api_key=...),
    AnthropicTranslator(model="claude-3-opus", api_key=...),
])

# Use cost-aware routing
router.set_strategy(RouterStrategy.COST_AWARE)

# Print metrics
print(router.print_metrics())
```

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

### New in DocTranslate

**Multi-Translator Router** (`doctranslate/translator/router.py`):
- Coordinates multiple translation backends
- Implements strategies: failover, round-robin, least-loaded, cost-aware
- Tracks per-translator metrics: success rate, cost, latency
- Automatic quality scoring via back-translation

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

# Install in development mode with test dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

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
- Use multi-translator router with `LEAST_LOADED` strategy to distribute load
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

## 📊 Metrics & Monitoring

DocTranslate's multi-translator router provides detailed metrics:

```python
router = TranslatorRouter([...])
metrics = router.get_metrics()

for name, stats in metrics.items():
    print(f"{name}:")
    print(f"  Success rate: {stats.success_rate:.1f}%")
    print(f"  Cost: ${stats.total_cost:.4f}")
    print(f"  Latency: {stats.avg_latency_ms:.2f}ms")
```

Monitor these metrics to optimize your translation pipeline and reduce costs.

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
