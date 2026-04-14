# Public API policy

This document defines what downstream repositories may rely on under semantic versioning.

## Stable (semver-guaranteed)

These symbols and their **documented** behaviors are stable within a major version:

- **`doctranslate.api`** — symbols in `doctranslate.api.__all__`, including:
  - `translate`, `async_translate`, `validate_request`, `inspect_input`
  - `build_translators`, `resolve_openai_api_key`, `TranslatorBuildResult`
  - `TranslationConfig`, `TranslateResult` (legacy runtime types)
  - `TranslationRequest`, `TranslationResult`, `PUBLIC_SCHEMA_VERSION`
- **`doctranslate.schemas`** — Pydantic models and enums re-exported from `doctranslate.schemas.__all__`, including:
  - `TranslationRequest`, `TranslationResult`, `TranslationOptions`, `TranslatorRequestConfig`
  - Progress / CLI helper types: `progress_event_from_dict`, `CliProgressLine`, `CliJsonEnvelope`
  - Router/TOML types: `NestedTranslatorConfig`, helpers such as `load_nested_translator_config`
- **Schema versions** — constants `PUBLIC_SCHEMA_VERSION` and `PROGRESS_EVENT_VERSION` in `doctranslate.schemas.versions`.

### Breaking changes (major bump)

- Removing or renaming any symbol in the stable lists above.
- Changing required fields or enum **values** on public Pydantic models.
- Changing the meaning of progress event `type` values or removing `schema_version` / `event_version` from emitted events.
- Changing the JSON envelope shape for `--output-format json` (top-level keys documented for CLI).

### Non-breaking (minor / patch)

- Adding **optional** fields to public Pydantic models.
- Adding new optional CLI flags.
- Adding new `ArtifactKind` values (consumers should tolerate unknown kinds).

## Internal (not semver-stable)

Do **not** import these for product integrations:

- `doctranslate.format.*` (including `doctranslate.format.pdf.high_level` except via `doctranslate.api` / `doctranslate.engine` shims).
- `doctranslate.progress_monitor`, `doctranslate.asynchronize`, provider-specific modules.
- IL dataclasses under `doctranslate.format.pdf.document_il` except through documented extension points.

Deep imports may continue to work but can change in minor releases.

## Compatibility shims (deprecated)

- **`doctranslate.engine`** — re-exports pipeline entrypoints; prefer `doctranslate.api`.
- **`doctranslate.pdf`** — re-exports PDF pipeline; prefer `doctranslate.api`.

## Experimental

- **`doctranslate.experimental`** — no stability guarantees; do not rely on it from external services.

## Schema versioning

- **`PUBLIC_SCHEMA_VERSION`** applies to `TranslationRequest`, `TranslationResult`, and CLI JSON envelopes.
- **`PROGRESS_EVENT_VERSION`** applies to streaming progress objects normalized by `progress_event_from_dict`.

Clients should reject unknown major schema versions when strict compatibility is required.
