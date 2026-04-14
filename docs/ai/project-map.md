# Project map (for humans and coding agents)

DocTranslater is a Python 3.10+ package (PyPI name **DocTranslater**; import package `doctranslate`): CLI entries `doctranslate` / `doctranslater` → `doctranslate.main:cli`. This fork extends upstream with multi-provider routing and local translation.

## Key directories

| Path | Role |
|------|------|
| `doctranslate/main.py` | Thin entry: `cli()` → `cli/dispatch.py`; `create_parser` aliases legacy parser. |
| `doctranslate/cli/` | vNext subcommands (`translate`, `assets`, `config`, …), argv mapping, JSON output helpers. |
| `doctranslate/cli/legacy_parser.py` | Flat `configargparse` surface (legacy + tests). |
| `doctranslate/cli/translate_run.py` | Shared async translation pipeline + progress UI. |
| `doctranslate/format/pdf/high_level.py` | PDF translation orchestration; `TRANSLATE_STAGES`; async/thread boundaries. |
| `doctranslate/format/pdf/document_il/` | Intermediate representation (IL): frontend/midend/backend, typesetting, translators. |
| `doctranslate/translator/` | Translator modes: OpenAI legacy, `TranslatorRouter`, LiteLLM executors, local → synthetic router. |
| `doctranslate/assets/` | Model/asset download, warmup, offline asset pack. |
| `tests/` | Pytest; mirror new behavior with focused tests. |
| `docs/` | MkDocs Material site; keep CLI/config docs in sync with code. |

## Authoritative vs generated (IL)

- **Edit by hand:** `doctranslate/format/pdf/document_il/il_version_1.rnc` (schema source).
- **Do not edit manually:** `il_version_1.rng`, `il_version_1.xsd`, `il_version_1.py` — regenerate per [Contributing](../CONTRIBUTING.md) (trang + xsdata).

## Where to change common behavior

| Task | Start here |
|------|------------|
| New CLI flag or default | vNext: `doctranslate/cli/vnext_argv.py` + passthrough; legacy: `doctranslate/cli/legacy_parser.py`. |
| Router / TOML / local knobs | `doctranslate/translator/config.py`, `factory.py`, `local_config.py`, `router.py`. |
| PDF stage order or wiring | `doctranslate/format/pdf/high_level.py` and stage classes under `document_il/`. |
| Public docs for config | `docs/configuration.md`, `docs/multi-translator.md`, `docs/local-translation.md`, `README.md`. |

## Logging

Use `log.debug()` (or appropriate logger levels), not `print()`, per [Contributing](../CONTRIBUTING.md).

## Contribution boundaries

Read [Contributing](../CONTRIBUTING.md): small PRs, English-only PRs/docs, no prompt-only PRs, translator/GUI policy. Open an issue before large changes.
