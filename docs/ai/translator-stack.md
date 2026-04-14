# Translator stack

Three CLI-facing modes (see `doctranslate.translator.factory.build_translators`):

## 1. Legacy OpenAI (`--translator openai`)

- Builds one or two `OpenAITranslator` instances from CLI `--openai*` flags and env (`OPENAI_API_KEY`, etc.).
- Use for single-provider OpenAI-compatible setups without nested TOML.
- **Transport:** `OpenAITranslator` delegates to `OpenAILLMTransport` (`doctranslate/translator/providers/openai_client.py`): for the default OpenAI host (no custom `--openai-base-url`), **Responses API** is tried first for plain text; **chat completions** are used for JSON mode, Pydantic **structured parse** (`chat.completions.parse`) when the pipeline passes `structured_response_model` in `rate_limit_params`, and as fallback if Responses fails or the gateway is custom / OpenAI-compatible.
- Shared helpers: token usage normalization and JSON cleanup live under `doctranslate/translator/llm/`.

## 2. Router (`--translator router`)

- Requires `--config` TOML with `[doctranslate]`, nested `profiles`, and `providers`.
- Loads `NestedTranslatorConfig` via `load_nested_translator_config`; validates with `validate_router_config`.
- Builds **two** `TranslatorRouter` instances: paragraph profile (`routing_profile`) and term extraction profile (`term_extraction_profile`).
- Strategies: `failover`, `round_robin`, `least_loaded`, `cost_aware`. Failover respects `fallback_on` and content-filter policy.
- Details: [Configuration](../configuration.md), [Multi-provider routing](../multi-translator.md).

## 3. Local (`--translator local`)

- Single-machine / LAN backends: Ollama, vLLM, llama-cpp server, OpenAI-compatible URL.
- `local_config.convert_local_translator_to_router_nested` expands **local → synthetic router** config, then same router path as (2).
- Batching: `--local-*-batch-*` flags and TOML keys map into translation config batch limits in `main.py`.
- Details: [Local translation](../local-translation.md).

## Config merge (router / nested TOML)

Documented in [Configuration](../configuration.md): defaults → TOML `[doctranslate]` → env for `api_key_env` → CLI overrides for router-only flags.

## Pitfalls for agents

- Do not assume “translator” means only OpenAI; check `translator_mode` and `build_translators` dispatch.
- Term extraction often needs **JSON-capable** providers; profiles may set `require_json_mode = true`.
- Changing provider ids, models, or base URLs affects **cache keys**; tests or users may need `--ignore-cache`.
- After changing flags or TOML schema, update **docs** and **tests** under `tests/test_translator_*`, `tests/test_local_*`, `tests/test_main_cli_*` as appropriate.
