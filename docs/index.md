# DocTranslater

**High-quality PDF translation** with layout preservation, multi-provider LLM routing, and local OpenAI-compatible backends.

This documentation site tracks the **[miguelenes/doctranslate](https://github.com/miguelenes/doctranslate)** fork. Upstream lineage: [funstory-ai/DocTranslate](https://github.com/funstory-ai/DocTranslate) (AGPL-3.0).

---

## Quick start

```bash
git clone https://github.com/miguelenes/doctranslate.git
cd doctranslate
uv sync --locked --group dev --extra full
uv run doctranslate --help
```

**Translate with OpenAI-compatible API:**

```bash
export OPENAI_API_KEY=sk-...
uv run doctranslate translate input.pdf --provider openai \
  --source-lang en --target-lang zh -o ./out
```

**Local (Ollama):** see [Local translation](local-translation.md).

---

## Explore the docs

| Topic | Description |
|-------|-------------|
| [Configuration](configuration.md) | CLI flags, TOML `[doctranslate]`, env vars, cache |
| [Multi-provider routing](multi-translator.md) | Router profiles, failover, metrics |
| [Local translation](local-translation.md) | Ollama, vLLM, OpenAI-compatible servers |
| [Supported languages](supported_languages.md) | Language codes and coverage |
| [Implementation details](ImplementationDetails/README.md) | PDF → IL → PDF pipeline stages |

---

## Highlights

- **Router** — OpenAI, Anthropic, OpenRouter, Ollama, and OpenAI-compatible gateways with strategies (`failover`, `round_robin`, `least_loaded`, `cost_aware`).
- **Local mode** — Same router core with a synthetic single-host profile for desktop and LAN servers.
- **IL pipeline** — Structured intermediate representation for parsing, layout, translation, typesetting, and PDF creation.

---

## Contributing

See [Contributing](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md). Issues and PRs for **this fork**: [github.com/miguelenes/doctranslate](https://github.com/miguelenes/doctranslate).

---

## License

DocTranslater is licensed under **AGPL-3.0**. See the repository `LICENSE` file.
