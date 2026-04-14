# Async Translation API

> [!NOTE]
> This documentation may contain AI-generated content. While we strive for accuracy, there might be inaccuracies. Please report any issues via:
>
> - [GitHub Issues](https://github.com/miguelenes/doctranslate/issues)
> - Community contribution (PRs welcome!)

## Overview

The `doctranslate.api.async_translate` coroutine provides an **asynchronous progress API** around the same **synchronous** PDF translation pipeline: workers still run blocking `translate` / `llm_translate` calls (often via thread pools). Use this entry point when you need `async for` progress events (CLI and UIs), not because the LLM stack is natively async end-to-end.

Stable import:

```python
from doctranslate.api import async_translate, validate_request
```

Legacy import (not semver-stable across minors):

```python
from doctranslate.format.pdf.high_level import async_translate
from doctranslate.format.pdf.translation_config import TranslationConfig
```

## Usage

```python linenums="1"
async def translate_with_progress():
    req = validate_request(
        {
            "input_pdf": "example.pdf",
            "lang_in": "en",
            "lang_out": "zh",
            "translator": {"mode": "openai", "openai": {"model": "gpt-4o-mini"}},
        }
    )

    try:
        async for event in async_translate(req):
            if event["type"] == "progress_update":
                print(f"Progress: {event['overall_progress']}%")
            elif event["type"] == "finish":
                summary = event["translation_result"]["summary"]
                print(f"Translation completed: {summary['original_pdf_path']}")
            elif event["type"] == "error":
                print(f"Error occurred: {event['error']}")
                break
    except asyncio.CancelledError:
        print("Translation was cancelled")
    except KeyboardInterrupt:
        print("Translation was interrupted")
```

## Event Types

The function yields different types of events during the translation process:

### 1. Progress Start Event

Emitted when a translation stage begins:

```python
{
    "type": "progress_start",
    "stage": str,              # Name of the current stage
    "stage_progress": float,   # Always 0.0
    "stage_current": int,      # Current progress count (0)
    "stage_total": int         # Total items to process in this stage
}
```

### 2. Progress Update Event

Emitted periodically during translation (controlled by report_interval, default 0.1s):

```python
{
    "type": "progress_update",
    "stage": str,              # Name of the current stage
    "stage_progress": float,   # Progress percentage of current stage (0-100)
    "stage_current": int,      # Current items processed in this stage
    "stage_total": int,        # Total items to process in this stage
    "overall_progress": float  # Overall translation progress (0-100)
}
```

### 3. Progress End Event

Emitted when a stage completes:

```python
{
    "type": "progress_end",
    "stage": str,              # Name of the completed stage
    "stage_progress": float,   # Always 100.0
    "stage_current": int,      # Equal to stage_total
    "stage_total": int,        # Total items processed in this stage
    "overall_progress": float  # Overall translation progress (0-100)
}
```

### 4. Finish Event

Emitted when translation completes successfully:

```python
{
    "type": "finish",
    "schema_version": "1",
    "event_version": "1",
    "translation_result": {
        "schema_version": "1",
        "summary": {...},
        "artifacts": {"items": [...]},
    },
}
```

When you pass a legacy `TranslationConfig` to `async_translate`, the dict may
still contain a live `translate_result` object for backward compatibility; prefer
`TranslationRequest` for stable wire-format output.

### 5. Error Event

Emitted if an error occurs during translation:

```python
{
    "type": "error",
    "schema_version": "1",
    "event_version": "1",
    "error": {
        "code": "internal_error",
        "message": "…",
        "retryable": false,
        "details": {},
    },
}
```

## Translation Stages

The translation process goes through the following stages in order:

1. ILCreater
2. LayoutParser
3. ParagraphFinder
4. StylesAndFormulas
5. ILTranslator
6. Typesetting
7. FontMapper
8. PDFCreater

Each stage will emit its own set of progress events.

## Cancellation

The translation process can be cancelled in several ways:

1. By raising a `CancelledError` (e.g., when using `asyncio.Task.cancel()`)
2. Through `KeyboardInterrupt` (e.g., when user presses Ctrl+C)
3. By calling `translation_config.cancel_translation()` on a legacy `TranslationConfig`
4. By cancelling the asyncio `Task` that consumes `async_translate` when using `TranslationRequest`

Example of programmatic cancellation (legacy `TranslationConfig`):

```python linenums="1"
async def translate_with_cancellation():
    config = TranslationConfig(
        input_file="example.pdf",
        translator=your_translator,
        # ... other configuration options
    )

    try:
        translation_task = asyncio.create_task(process_translation(config))
        await asyncio.sleep(5)
        config.cancel_translation()
        await translation_task
    except asyncio.CancelledError:
        print("Translation was cancelled")

async def process_translation(config):
    async for event in async_translate(config):
        if event["type"] == "error":
            err = event.get("error")
            if isinstance(err, dict) and err.get("code") == "canceled":
                print("Translation was canceled")
                break
            print(f"Error occurred: {err}")
            break
        # ... handle other events ...
```

When cancelled:
- The function will log the cancellation reason
- All resources will be cleaned up properly
- Any ongoing translation tasks will be stopped
- A final error event with `CancelledError` will be emitted
- The function will exit gracefully

## Error Handling

Any errors during translation will be:
1. Logged with full traceback (if debug mode is enabled)
2. Reported through an error event
3. Cause the event stream to stop after the error event
4. Clean up resources properly before exiting

It's recommended to handle these events appropriately in your application to provide feedback to users. The example in the Usage section shows a basic error handling pattern. 