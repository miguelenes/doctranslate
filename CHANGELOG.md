# Changelog

## 0.6.0

### Breaking

- **CLI:** flat argv (`--files`, `--warmup`, …) removed; use subcommands (`translate`, `assets`, …). See [docs/migration.md](docs/migration.md).
- **TOML:** `[babeldoc]` sections are no longer read; use `[doctranslate]` only.
- **Dependencies:** `configargparse` removed (pure `argparse` CLI).
- **Console scripts:** `doctranslater` and `doc-translater` entry points removed (`doctranslate`, `doc-translate` remain).
- **`TranslationConfig`:** constructor now takes `TranslationSettings` instead of a long keyword list.
- **`TranslateResult`:** fields renamed to `mono_plain_pdf`, `mono_watermarked_pdf`, `dual_plain_pdf`, `dual_watermarked_pdf`.
- **Exceptions:** `doctranslate.exceptions` is the public module; `PriorTranslatedInputError` replaces `InputFileGeneratedByBabelDOCError`; `babeldoc_exception` / `doctranslate_exception` packages removed.
- **TM:** automatic import of legacy `cache.v1.db` on DB init removed; use `doctranslate tm migrate-v1-cache`.

### Removed flags / behavior

- `--enhance-compatibility`, `--no-watermark`, ignored `font`, and related `TranslationConfig` compatibility branches.
