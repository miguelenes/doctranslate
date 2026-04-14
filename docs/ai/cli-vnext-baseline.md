# CLI vNext baseline (frozen inventory)

This document freezes the pre–vNext refactor surface for migration work. The implementation lives under `doctranslate/cli/`; the legacy flat parser is `doctranslate/cli/legacy_parser.py` (`create_legacy_parser`, exposed as `doctranslate.main.create_parser`).

## Legacy flat flags (single parser)

All options previously defined in `doctranslate/main.py#create_parser` now live in `legacy_parser.py`. Categories:

- **Global / lifecycle:** `--config`, `--version`, `--files`, `--debug`, `--warmup`, `--generate-offline-assets`, `--restore-offline-assets`, `--working-dir`, `--metadata-extra-data`, `--enable-process-pool`, `--rpc-doclayout*`
- **Translation:** languages, pages, QPS, compatibility, watermark (including deprecated `--no-watermark`), OCR, glossary, TM, rendering, skip modes, pool workers, etc.
- **OpenAI:** `--openai` gate, `--openai-*`, term extraction overrides, JSON/temperature/reasoning flags
- **Router / local:** `--translator`, routing overrides, `--validate-translators`, full `--local-*` set

## Docs / test mismatches (addressed in vNext rollout)

- README troubleshooting previously referenced non-existent flags (`--split-pages` vs `--max-pages-per-part`, `--watermark` vs `--watermark-output-mode`, `--font-fallback`). Migration and README should use vNext names where applicable.
- CI invoked only `doctranslate`; vNext CI also exercises `doc-translate` and `assets` subcommands.

## vNext command entry

- Router: `should_use_vnext()` in `doctranslate/cli/dispatch.py` — legacy triggers include `--files`, `--warmup`, `--openai`, `--translator`, etc.
- Subcommands: `translate`, `inspect`, `glossary`, `tm`, `assets`, `debug`, `config`.
