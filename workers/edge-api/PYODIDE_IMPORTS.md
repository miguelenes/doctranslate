# Pyodide import audit (edge worker)

This document satisfies the **import audit** step for running DocTranslater types on Cloudflare Python Workers.

## Prefer light imports (required for this worker)

Do **not** use `import doctranslate.schemas` in Workers: that runs [doctranslate/schemas/__init__.py](../../doctranslate/schemas/__init__.py) and loads the full barrel (`translator.config`, `TranslationSettings` re-exports, etc.).

Use these modules only:

| Import path | Role |
|-------------|------|
| `doctranslate.schemas.public_api` | Warmup import + `TranslationRequest` for `translation_request` JSON validation |
| `doctranslate.schemas.versions` | `PUBLIC_SCHEMA_VERSION` when building test payloads |

## What the worker imports from DocTranslater

| Import path | Role |
|-------------|------|
| `doctranslate.schemas.public_api` | Package import in `/edge/v1/schema-warmup`; `TranslationRequest` in forwarding |
| `doctranslate.schemas.versions` | `PUBLIC_SCHEMA_VERSION` in warmup response |

Those code paths load **public_api** (nested Pydantic models, enums, versions) and **not** the PDF engine or `doctranslate.api`.

## Base distribution dependencies (from root `pyproject.toml`)

Installed automatically with `DocTranslater` without extras:

- `charset-normalizer`, `chardet`, `pydantic`, `regex`, `toml`

Each must remain compatible with **Pyodide** in your target `compatibility_date`. If `uv run pywrangler dev` fails at import time, bisect by temporarily removing the path dependency and re-adding modules.

## Verification commands

```bash
cd workers/edge-api
uv sync --group dev
uv run pytest tests/ -q
uv run pywrangler dev   # manual: open /edge/v1/schema-warmup
```
