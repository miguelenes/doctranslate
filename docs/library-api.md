# Stable library API

DocTranslater exposes a **versioned** Python API for embedding translation in other applications. Prefer these entry points over deep imports under `doctranslate.format.pdf`.

## Install

```bash
pip install "DocTranslater[full]"
```

## Canonical imports

| Purpose | Module |
|--------|--------|
| Translate, async progress, inspect, validate | `doctranslate.api` |
| Request/result/event Pydantic models | `doctranslate.schemas` (also re-exported from `doctranslate.api` where noted) |

## Translation request (JSON-serializable)

Build a `TranslationRequest` (see `doctranslate.schemas` and `doctranslate/schemas/public_api.py` in the repo). Minimal OpenAI example:

```python
from pathlib import Path

from doctranslate.api import translate, validate_request

req = validate_request(
    {
        "input_pdf": str(Path("input.pdf").resolve()),
        "lang_in": "en",
        "lang_out": "zh",
        "translator": {
            "mode": "openai",
            "ignore_cache": False,
            "openai": {
                "model": "gpt-4o-mini",
                "api_key": None,  # use OPENAI_API_KEY if omitted
            },
        },
        "options": {
            "output_dir": str(Path("./out").resolve()),
            "qps": 4,
        },
    }
)

result = translate(req)
print(result.summary.original_pdf_path)
for a in result.artifacts.items:
    print(a.kind, a.path, a.sha256)
```

## Async progress

```python
import asyncio
from pathlib import Path

from doctranslate.api import async_translate, validate_request

async def main() -> None:
    req = validate_request(
        {
            "input_pdf": str(Path("input.pdf").resolve()),
            "lang_in": "en",
            "lang_out": "zh",
            "translator": {"mode": "openai", "openai": {"model": "gpt-4o-mini"}},
            "options": {"output_dir": str(Path("./out").resolve())},
        }
    )
    async for event in async_translate(req):
        if event["type"] == "progress_update":
            print(event["overall_progress"])
        elif event["type"] == "finish":
            print(event["translation_result"]["summary"])
        elif event["type"] == "error":
            print(event["error"])
            break

asyncio.run(main())
```

Each event dict includes `schema_version` and `event_version` for forward compatibility.

## Validate configuration only

```python
from doctranslate.api import validate_request

validate_request(Path("request.json"))
```

## Inspect PDFs (no LLM)

```python
from doctranslate.api import inspect_input

info = inspect_input(["./doc.pdf"])
for f in info.files:
    print(f.path, f.page_count, f.prior_translated_marker)
```

## CLI: JSON request file

For subprocess integration, write a `TranslationRequest` JSON file and run:

```bash
doctranslate --output-format json translate \
  --request-json request.json \
  --emit-progress-json
```

- With `--emit-progress-json`, stdout receives NDJSON lines with `stream: "progress"` followed by the usual final JSON envelope from `--output-format json`.
- You can also place `--output-format json` immediately after `translate` (see `doctranslate translate --help`).

## Legacy `TranslationConfig`

Existing code may still pass `TranslationConfig` to `translate` / `async_translate`. That path returns the legacy runtime result type and is supported for compatibility; new integrations should use `TranslationRequest` and `TranslationResult`.

## Further reading

- [Public API policy](public-api-policy.md) — semver boundaries and breaking-change rules.
- [Package layers](ai/package-layers.md) — optional extras and minimal installs.
