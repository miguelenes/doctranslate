# Multi-provider routing

DocTranslater can route LLM calls through a **sync** `TranslatorRouter` that selects among several LiteLLM-backed providers using a TOML-defined **profile** (ordered provider list + strategy + failure policy).

## When to use `--translator local`

Use **local** mode when you want a single-machine or LAN **Ollama**, **vLLM**, or **OpenAI-compatible** server without editing nested `profiles` / `providers` tables. It expands internally to the same router + LiteLLM path as multi-provider mode. See [Local translation](local-translation.md).

## When to use `--translator router`

Use router mode when you want:

- Failover across OpenAI, Anthropic, OpenRouter, OpenAI-compatible gateways, or local **Ollama**
- Separate **translation** vs **term extraction** profiles (e.g. JSON-only backends for glossary extraction)
- Per-provider metrics (requests, latency, tokens, estimated cost) at end of run

Requirements:

- `--config` pointing to a TOML file with `[doctranslate]`, `profiles`, and `providers` (see [Configuration](configuration.md)).
- Valid API keys in the environment for providers that need them.

Legacy workflows keep using `--translator openai` (default) with `--openai` and related flags.

**Translation memory** (`--tm-mode`, etc.) applies to any translator mode once enabled; cache keys still include the router fingerprint (profile, strategy, per-provider fields). See [Translation memory](translation-memory.md).

## Strategies

| Strategy | Behavior (simplified) |
|----------|------------------------|
| `failover` | Walk the profile’s `providers` order; on recoverable failures in `fallback_on`, try the next provider until success or `max_attempts`. |
| `round_robin` | Rotate starting provider per request. |
| `least_loaded` | Prefer provider with fewer concurrent in-flight calls when possible. |
| `cost_aware` | Prefer cheaper estimated next-token cost when usage and price hints are available. |

Global `routing_strategy` in TOML can be overridden per profile or via `--routing-strategy`.

## Failure handling

Failures are classified (e.g. `rate_limit`, `timeout`, `authentication`, `malformed_response`, `content_filter`, `unknown`). The router only **fails over** when the category is listed in the profile’s `fallback_on`. Auth-style failures typically mark the provider unhealthy for the run so it is not selected again.

**Content filtering:** By default profiles do not allow silently falling back to another provider on content-filter errors unless `allow_content_filter_fallback` is enabled in that profile.

## Term extraction profile

Automatic glossary term extraction issues JSON-shaped prompts. Define a profile with `require_json_mode = true` and list providers that support JSON mode. Set `term_extraction_profile` in TOML (or `--term-extraction-profile`) to that profile name. Paragraph translation can use a different `routing_profile` with cheaper or faster models.

**Structured outputs:** With `--translator openai`, term extraction and batched LLM paragraph translation can use OpenAI `chat.completions.parse` when `supports_structured_outputs` is true (default for common providers in router config). Router / LiteLLM paths continue to use `response_format: json_object` unless you add future schema support in provider configs.

## Metrics

With `metrics_output = "json"` or `both`, and `metrics_json_path` set (or overridden by CLI), the router can write structured usage summaries. Logs always include a human-readable summary when `log` or `both` is selected.

When **Prometheus** metrics are enabled for the process (`DOCTRANSLATE_METRICS_ENABLED`, see [Observability](observability.md)), the same router emits labeled **service** counters and histograms (outcomes, latency, tokens, estimated cost) alongside these end-of-run summaries—use one or both depending on whether you need files/logs vs scrape targets.

## Example

```bash
doctranslate -c doctranslate.toml translate input.pdf \
  --translator router \
  --lang-in en --lang-out zh \
  -o ./out
```

Validate config without translating:

```bash
doctranslate config validate --translator router -c doctranslate.toml
```

## Programmatic use

For **application embedding**, prefer `doctranslate.api` with a `TranslationRequest` whose `translator.mode` is `router` or `local`, or use `doctranslate.api.build_translators` when you need low-level `BaseTranslator` instances (see [Stable library API](library-api.md)).

For **tests or advanced composition**, you may call `doctranslate.translator.factory.build_translators` with `translator_mode="router"` and a config path, or construct `TranslatorRouter` with pre-built `LiteLLMProviderExecutor` instances.

The public PDF pipeline still calls **`translate` / `llm_translate` synchronously** on the translator instance; there is no requirement to use `async` in your own code for translation itself. Progress reporting uses `doctranslate.api.async_translate` around thread-pooled work (see [Async Translation API](ImplementationDetails/AsyncTranslate/AsyncTranslate.md)).
