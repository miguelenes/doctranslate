# Troubleshooting

Common problems when installing, translating, or contributing. For CLI flags and TOML, see [Configuration](configuration.md).

## Installation

**`No module named 'doctranslate'`**

- From a clone: `uv sync --locked --group dev --extra full` then `uv run doctranslate --version`.
- From PyPI: `pip install "DocTranslater[full]"` in the environment you run.

**`ImportError` for PyMuPDF, onnx, OpenAI, etc.**

- The minimal PyPI install is small on purpose. Use extras: [Package layers](ai/package-layers.md). For the full CLI path, install **`DocTranslater[full]`**.

**Docker: wrong image profile or missing native libraries**

- Use the target that matches your workload: see [Docker](docker.md) and [Docker image profiles](docker-profiles.md). OCR and Hyperscan-backed glossary paths need **`runtime-vision`** (or a custom build) rather than the default **`runtime-cpu`** layer set.
- Warm builds need outbound HTTPS during `docker build`; use non-warm targets and `doctranslate assets warmup` at runtime if the build network is restricted.

**Tracked `examples/` or `*.pdf` missing locally**

- The repo `.gitignore` ignores `examples/` and `*.pdf` for **untracked** files. CI and clones still include committed paths such as `examples/ci/test.pdf`. If you need that file, ensure you did a full `git clone` (not a sparse checkout that omits `examples/`).

## Translation runs

**Translation is slow**

- Router: try `least_loaded` or `cost_aware` where appropriate (see [Multi-provider routing](multi-translator.md)).
- Split large jobs: `doctranslate translate … --split-pages N` (alias `--max-pages-per-part`).
- Use a faster (sometimes lower-quality) model for drafts.

**Layout looks wrong after translation**

- Tune fonts with `--primary-font-family` (see `doctranslate translate --help`).
- Try `--watermark-mode no_watermark` (alias `--watermark-output-mode`).
- Image-only scans need OCR — see `--ocr-mode` in [Configuration](configuration.md).

**`LocalPreflightError` / cannot reach Ollama (local mode)**

- See [Local translation](local-translation.md) — `ollama serve`, `--local-base-url`, and model names must match what the server exposes.

**Wrong cache hits after changing model**

- Cache keys include provider id, model, and base URL. Use `--ignore-cache` when comparing models.

## Translation memory

**Database locked or TM errors**

- Only one writer per TM SQLite file; avoid running two translates on the same cache path concurrently.
- See [Translation memory](translation-memory.md) for migration from legacy cache layouts.

## Documentation builds

**MkDocs strict fails but Zensical passes (or the reverse)**

- CI runs **MkDocs strict** in the test workflow and **Zensical** for Pages. Run both locally: [Verification](ai/verification.md).

## Getting help

- [Contributing](CONTRIBUTING.md) and [open an issue](https://github.com/miguelenes/doctranslate/issues).
