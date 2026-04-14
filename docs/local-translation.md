# Local translation

Translate PDFs using **models on your machine** or on a **LAN-hosted OpenAI-compatible server**, without calling hosted APIs (OpenAI, Anthropic, etc.).

DocTranslate’s PDF pipeline still expects an **LLM** that can follow structured prompts and, where needed, **JSON output** (paragraph translation and automatic term extraction). This is not the same workflow as classic sentence-MT engines (e.g. Marian via CTranslate2); support for that may be added later.

## Quick start (Ollama)

1. Install [Ollama](https://ollama.com/) and pull a model, for example:

   ```bash
   ollama pull qwen2.5:7b
   ```

2. Run DocTranslate:

   ```bash
   doctranslate --translator local \
     --local-backend ollama \
     --local-model qwen2.5:7b \
     --files input.pdf --lang-in en --lang-out zh \
     --output ./out
   ```

3. Validate configuration and reachability (no PDF required):

   ```bash
   doctranslate --translator local --validate-translators \
     --local-backend ollama --local-model qwen2.5:7b
   ```

Optional **translation memory** flags (`--tm-mode`, …) apply the same way in local mode as for the router; see [Translation memory](translation-memory.md).

## Backends

| Preset | What it uses | When to use |
|--------|----------------|-------------|
| `ollama` | Native Ollama HTTP API via LiteLLM | Easiest desktop setup; CPU or modest GPU |
| `vllm` | OpenAI-compatible `/v1` on your server (default base `http://127.0.0.1:8000/v1`) | High throughput on NVIDIA GPUs |
| `llama-cpp` | Same as OpenAI-compatible; point `--local-base-url` at `llama-cpp-python` server | Offline GGUF, Apple Silicon / CPU friendly |
| `openai-compatible` | Explicit OpenAI-compatible gateway | Custom local or LAN URL |

**Note:** `glm-ocr` and similar **vision / OCR** models are for document *reading* / OCR experiments, not for replacing the main paragraph translation model. Use instruct / chat models suited to translation and JSON.

## OpenAI-compatible server (vLLM, llama-cpp-python)

Start your server (examples only; see upstream docs for flags):

```bash
# vLLM (example)
vllm serve Qwen/Qwen2.5-7B-Instruct --host 0.0.0.0 --port 8000
```

```bash
# llama-cpp-python server (example)
python3 -m llama_cpp.server --model /path/to/model.gguf --host 0.0.0.0 --port 8080
```

Then run DocTranslate with a base URL that includes `/v1` (or omit `/v1`; DocTranslate normalizes it):

```bash
doctranslate --translator local \
  --local-backend vllm \
  --local-base-url http://127.0.0.1:8000 \
  --local-model Qwen/Qwen2.5-7B-Instruct \
  --files input.pdf --lang-in en --lang-out de
```

Many local servers accept a dummy API key; DocTranslate sends `EMPTY` when none is configured.

## Configuration file (TOML)

You can set the same knobs under `[doctranslate]` or under `[doctranslate.local]`:

```toml
[doctranslate]
translator = "local"
local_backend = "ollama"
local_model = "qwen2.5:7b"
local_timeout_seconds = 120
local_translation_batch_tokens = 256
local_translation_batch_paragraphs = 4
local_term_batch_tokens = 400
local_term_batch_paragraphs = 8

[doctranslate.local]
# Alternative nested form (overrides duplicate keys in [doctranslate] when both set)
term_model = "qwen2.5:3b"
```

Then:

```bash
doctranslate --translator local -c doctranslate.toml --files input.pdf
```

CLI flags override TOML values when both are present.

## Batching and performance

The IL translator batches paragraphs before each LLM call. Defaults match the previous hard-coded behavior:

- Translation: flush when estimated tokens **> 200** or paragraphs **> 5**
- Term extraction: **> 600** tokens or **> 12** paragraphs

Tune with:

- `--local-translation-batch-tokens` / `--local-translation-batch-paragraphs`
- `--local-term-batch-tokens` / `--local-term-batch-paragraphs`

Smaller models or tight GPU memory: **lower** batch tokens and **disable** automatic glossary extraction (`--no-auto-extract-glossary`) if JSON term extraction is flaky.

## Hardware hints

- **CPU-only:** prefer smaller quantized instruct models (e.g. 3B–7B class); reduce batch sizes and concurrency (`--qps`, `--pool-max-workers`).
- **Apple Silicon:** Ollama or llama-cpp with Metal; avoid expecting vLLM as the primary path on macOS.
- **NVIDIA + throughput:** run **vLLM** (or another OpenAI-compatible server) on a workstation or LAN host; increase `--pool-max-workers` cautiously to match server capacity.

`--local-context-window` is stored for documentation / future tuning; the pipeline still uses tiktoken-style estimates for batching.

## Troubleshooting

| Symptom | What to check |
|---------|----------------|
| `LocalPreflightError` / cannot reach Ollama | `ollama serve` running; `--local-base-url` matches your Ollama host |
| Model not found | `ollama pull <model>`; `GET /api/tags` lists the exact name (including tags) |
| JSON / term extraction failures | Smaller model struggling with `response_format`; disable auto glossary or use a larger term model (`--local-term-model`) |
| OOM or slow first request | Normal cold start; reduce batch tokens; smaller quant; server-side max context |
| Wrong cache hits after changing model | Cache keys include provider id + model + base URL; use `--ignore-cache` when comparing models |

## Benchmarks (manual)

Use the helper script (requires a real local server and sample PDF):

```bash
uv run python scripts/bench_local_translation.py \
  --pdf examples/ci/test.pdf \
  --lang-in en --lang-out zh \
  --backend ollama --model qwen2.5:7b
```

## See also

- [Configuration](configuration.md) — all CLI and TOML options
- [Multi-provider routing](multi-translator.md) — advanced failover and hosted + local mixes
