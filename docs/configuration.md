# Configuration

DocTranslate reads CLI flags first (via `configargparse`), and can merge a TOML file passed with `-c` / `--config`. For **multi-provider routing**, nested tables under **`[doctranslate]`** define providers and route profiles. Legacy configs may use **`[babeldoc]`** with the same nested shape; prefer `[doctranslate]` for new files (see [Migration](migration.md)).

## Merge order (router / nested TOML)

1. **Defaults** in code (`NestedTranslatorConfig`).
2. **TOML** `[doctranslate]` section (and nested `profiles` / `providers`). Nested router config loading also accepts `[babeldoc]` when `[doctranslate]` is absent.
3. **Environment** for API keys referenced by `api_key_env` on each provider.
4. **CLI overrides** for router-only flags (see below).

When both `[babeldoc]` and `[doctranslate]` appear in the same file, CLI defaults loaded from TOML merge **`babeldoc` first, then `doctranslate`** (later values win for duplicate keys).

Legacy **OpenAI-only** mode (`--translator openai`) does not require nested TOML; it uses `--openai*` flags and `OPENAI_*` environment variables.

## Local translation CLI flags

These apply when `--translator local` (see [Local translation](local-translation.md)):

| Flag | Description |
|------|-------------|
| `--local-backend` | `ollama`, `vllm`, `llama-cpp`, or `openai-compatible` (default: ollama when unset in TOML). |
| `--local-model` | Model id for paragraph translation (required unless set in TOML). |
| `--local-base-url` | OpenAI-compatible base URL (optional for Ollama; required for other backends). |
| `--local-term-model` | Optional separate model for automatic term extraction. |
| `--local-term-base-url` | Optional separate base URL for term extraction. |
| `--local-api-key` | Optional key for OpenAI-compatible servers. |
| `--local-timeout-seconds` | Request timeout (default 120 in synthetic config). |
| `--local-max-retries` | Passed to the HTTP client / LiteLLM retries (default 2). |
| `--local-context-window` | Hint only (optional). |
| `--local-translation-batch-tokens` / `--local-translation-batch-paragraphs` | Paragraph batching thresholds (defaults 200 / 5). |
| `--local-term-batch-tokens` / `--local-term-batch-paragraphs` | Term extraction batching (defaults 600 / 12). |

With `--validate-translators`, use `--translator local` to run configuration validation plus a quick reachability check (Ollama `/api/tags` or OpenAI-compatible `/v1/models`).

## Translation memory (TM)

Reuse policy for SQLite-backed translation cache: normalized keys, optional fuzzy and semantic layers. See **[Translation memory](translation-memory.md)** for modes, safety rules, and optional `tm_semantic` extras.

| Flag | Description |
|------|-------------|
| `--tm-mode` | `off` (default), `exact`, `fuzzy`, or `semantic`. |
| `--tm-scope` | `document`, `project`, or `global`. |
| `--tm-min-segment-chars` | Minimum source length for fuzzy/semantic reuse. |
| `--tm-fuzzy-min-score` | RapidFuzz `WRatio` threshold (0–100). |
| `--tm-semantic-min-similarity` | Cosine similarity floor for semantic reuse. |
| `--tm-project-id` | Optional project scope id. |
| `--tm-embedding-model` | Embedding model id when `--tm-mode=semantic`. |
| `--tm-import` | NDJSON path to merge into TM before translating. |
| `--tm-export` | NDJSON path or directory to export TM after each finished PDF. |

## Router CLI flags

These apply when `--translator router` and a valid `--config` is provided:

| Flag | Description |
|------|-------------|
| `--routing-profile` | Profile name for paragraph / IL translation (default from TOML `routing_profile`). |
| `--term-extraction-profile` | Profile for automatic term extraction (default `term_extraction_profile` in TOML). |
| `--routing-strategy` | Override strategy: `failover`, `round_robin`, `least_loaded`, `cost_aware`. |
| `--metrics-output` | `log`, `json`, or `both` for per-provider metrics at end of run. |
| `--metrics-json-path` | Path for JSON metrics when output includes `json`. |
| `--validate-translators` | Load and validate TOML only, then exit (no PDF). Requires `--config`. |

## Environment variables

### Legacy OpenAI path

- `OPENAI_API_KEY` — default API key if `--openai-api-key` is omitted.
- `OPENAI_BASE_URL` — optional gateway base URL.
- `OPENAI_MODEL` — optional default model name.

### Router providers

Each provider entry can set `api_key_env = "MY_KEY"`. The process environment must define that variable. Prefer `api_key_env` in TOML so secrets are not committed to version control.

## TOML schema (nested)

Top-level table `[doctranslate]`:

```toml
[doctranslate]
translator = "router"
lang_in = "en"
lang_out = "zh"
routing_profile = "translate"
term_extraction_profile = "terms"
routing_strategy = "failover"          # optional global default
metrics_output = "log"                 # log | json | both
metrics_json_path = ""               # path when metrics_output includes json
```

### Profiles (`[doctranslate.profiles.<name>]`)

- `providers` — ordered list of provider **ids** (strings).
- `strategy` — `failover`, `round_robin`, `least_loaded`, `cost_aware` (per-profile override).
- `fallback_on` — list of failure categories that trigger trying the next provider (e.g. `rate_limit`, `timeout`, `server_error`, `malformed_response`, `partial_outage`, `unknown`).
- `max_attempts` — cap on total attempts across the ordered provider list for one logical request.
- `require_json_mode` — if true, only providers with JSON capability are eligible (use for term extraction profiles).
- `require_reasoning`, `min_health_score`, `allow_content_filter_fallback` — optional policy knobs.

### Providers (`[doctranslate.providers.<id>]`)

- `provider` — one of: `openai`, `anthropic`, `openrouter`, `openai_compatible`, `ollama`.
- `model` — model id as expected by LiteLLM for that backend.
- `api_key_env` — name of environment variable holding the secret (recommended).
- `api_key` — inline key (discouraged for real deployments).
- `base_url` — optional (OpenAI-compatible gateways, Ollama host, etc.).
- `timeout_seconds`, `max_retries`, `rpm`, `tpm`, `max_output_tokens`
- `supports_json_mode`, `supports_structured_outputs`, `supports_reasoning`, `supports_streaming` — overrides when autodetection is wrong. Structured outputs indicate the provider can satisfy schema-style JSON (used when routing requests that attach a Pydantic response model; LiteLLM paths still use `json_object` where configured).
- `input_cost_per_million_tokens`, `output_cost_per_million_tokens` — for `cost_aware` routing when list prices are not built in.

### Ollama note

`ollama` providers do not require an API key in config validation when no `api_key_env` is set.

## Translation cache

The on-disk translation cache uses **`cache.v2.db`**. Cache keys include a provider / engine identifier (widened in v2). Changing provider ids or models may change cache keys.

## See also

- [Multi-provider routing](multi-translator.md) — strategies, failover behavior, metrics.
- [Supported languages](supported_languages.md)
