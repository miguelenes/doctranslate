# Project map (for humans and coding agents)

DocTranslater is a Python 3.10+ package (PyPI name **DocTranslater**; import package `doctranslate`): CLI entries `doctranslate` / `doc-translate` → `doctranslate.main:cli`. This fork extends upstream with multi-provider routing and local translation.

## Key directories

| Path | Role |
|------|------|
| `doctranslate/main.py` | Entry: `cli()` → `cli/dispatch.py`; `create_parser` → translate argparse parent (tests). |
| `doctranslate/api.py` | Stable public API (`translate`, `async_translate`, `validate_request`, `inspect_input`, `build_translators`, …); see [library API](../library-api.md). |
| `doctranslate/schemas/` | Pydantic public contracts (`TranslationRequest`, …) + router/TOML types; minimal deps. |
| `doctranslate/engine/service.py` | Orchestrates public requests → PDF pipeline (full extra). |
| `doctranslate/engine/adapters.py` | Maps public models ↔ runtime `TranslationSettings` / `TranslationConfig`. |
| `doctranslate/bootstrap.py` | Cache dir creation without importing the PDF/IL graph (used by CLI). |
| `doctranslate/cli/` | Subcommands (`translate`, `assets`, `config`, …), JSON output helpers. |
| `doctranslate/cli/translate_cli.py` | Argparse flags for `translate`. |
| `doctranslate/cli/translate_run.py` | Async translation pipeline + progress UI. |
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
| New CLI flag or default | `doctranslate/cli/translate_cli.py` (+ `dispatch.py` if root-level). |
| Router / TOML / local knobs | `doctranslate/translator/config.py`, `factory.py`, `local_config.py`, `router.py`. |
| PDF stage order or wiring | `doctranslate/format/pdf/high_level.py` and stage classes under `document_il/`. |
| Public docs for config | `docs/configuration.md`, `docs/multi-translator.md`, `docs/local-translation.md`, `README.md`. |

## Logging

Use `log.debug()` (or appropriate logger levels), not `print()`, per [Contributing](../CONTRIBUTING.md).

## Contribution boundaries

Read [Contributing](../CONTRIBUTING.md): small PRs, English-only PRs/docs, no prompt-only PRs, translator/GUI policy. Open an issue before large changes.
