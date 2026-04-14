# Migration and compatibility

## TOML configuration section

The CLI and nested translator configuration use the **`[doctranslate]`** table in TOML files.

**Legacy:** configs that used **`[babeldoc]`** (same schema) are still read for nested router/local settings when **`[doctranslate]`** is absent. Prefer `[doctranslate]` for new files.

CLI flags loaded from a config file merge sections in this order: **`babeldoc` first, then `doctranslate`** (later keys win). Use only one section to avoid surprises.

## Cache directory

Runtime cache defaults to `~/.cache/doctranslate`. There is no automatic migration from other tool cache folders; clear or ignore old directories if you are switching machines.

## Console entry points

The primary CLI is **`doctranslate`**. An additional kebab-case alias **`doc-translate`** may be installed for the same entry point (see `pyproject.toml` `[project.scripts]`).

## CLI vNext (subcommands)

DocTranslater routes invocations in two ways:

1. **vNext (default)** when the first real token is a subcommand such as `translate`, `assets`, `config`, …
2. **Legacy flat** when argv contains classic entry triggers such as `--files`, `--warmup`, `--openai`, `--translator`, … (a deprecation warning is logged).

### Common mappings

| Legacy | vNext |
|--------|--------|
| `doctranslate --warmup` | `doctranslate assets warmup` |
| `doctranslate --generate-offline-assets DIR` | `doctranslate assets pack-offline DIR` |
| `doctranslate --restore-offline-assets PATH` | `doctranslate assets restore-offline PATH` |
| `doctranslate --openai --files a.pdf …` | `doctranslate translate a.pdf --provider openai …` (no `--openai` gate) |
| `--lang-in` / `--lang-out` | `--source-lang` / `--target-lang` (aliases still accepted on `translate`) |
| `--qps` | `--request-rate` (alias `--qps`) |
| `--max-pages-per-part` | `--split-pages` |
| `--watermark-output-mode` | `--watermark-mode` |
| `--metrics-json-path` | `--metrics-file` |
| `--term-extraction-profile` | `--term-profile` |
| `--validate-translators --translator router --config f.toml` | `doctranslate config validate --translator router -c f.toml` |

Additional legacy flags can be passed **after** recognized `translate` options; they are forwarded to the legacy parser (e.g. `--ocr-mode hybrid`).

See [CLI vNext baseline](ai/cli-vnext-baseline.md) for the frozen inventory.

## Upstream

This repository is a fork of [funstory-ai/DocTranslate](https://github.com/funstory-ai/DocTranslate). Issue links in older docs may still reference upstream; use [miguelenes/doctranslate issues](https://github.com/miguelenes/doctranslate/issues) for this fork.
