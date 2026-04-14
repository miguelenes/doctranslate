"""Argparse surface for ``doctranslate translate`` (single parser, no ConfigArgParse)."""

from __future__ import annotations

import argparse


def build_translate_parent_parser() -> argparse.ArgumentParser:
    """All flags and positionals merged into the ``translate`` subcommand via ``parents=``."""
    parser = argparse.ArgumentParser(add_help=False)

    translation_group = parser.add_argument_group(
        "Translation",
        description="Used during translation",
    )
    translation_group.add_argument(
        "--pages",
        "-p",
        help="Pages to translate. If not set, translate all pages. like: 1,2,1-,-3,3-5",
    )
    translation_group.add_argument(
        "--min-text-length",
        type=int,
        default=5,
        help="Minimum text length to translate (default: 5)",
    )
    translation_group.add_argument(
        "--lang-in",
        "--source-lang",
        "-li",
        dest="lang_in",
        default="en",
        help="The code of source language.",
    )
    translation_group.add_argument(
        "--lang-out",
        "--target-lang",
        "-lo",
        dest="lang_out",
        default="zh",
        help="The code of target language.",
    )
    translation_group.add_argument(
        "--output",
        "--output-dir",
        "-o",
        dest="output",
        default=None,
        help="Output directory for files. if not set, use same as input.",
    )
    translation_group.add_argument(
        "--qps",
        "--request-rate",
        "-q",
        dest="qps",
        type=int,
        default=4,
        help="QPS limit of translation service",
    )
    translation_group.add_argument(
        "--ignore-cache",
        action="store_true",
        help="Ignore translation cache.",
    )
    translation_group.add_argument(
        "--tm-mode",
        choices=["off", "exact", "fuzzy", "semantic"],
        default="off",
        help=(
            "Translation memory: off=SQLite exact cache only; exact=+normalized TM keys; "
            "fuzzy=+RapidFuzz similarity; semantic=+optional embeddings (install sentence-transformers)."
        ),
    )
    translation_group.add_argument(
        "--tm-scope",
        choices=["document", "project", "global"],
        default="document",
        help="TM row visibility: document (default), project, or global pool.",
    )
    translation_group.add_argument(
        "--tm-min-segment-chars",
        type=int,
        default=12,
        help="Minimum source length for fuzzy/semantic TM reuse (default: 12).",
    )
    translation_group.add_argument(
        "--tm-fuzzy-min-score",
        type=float,
        default=92.0,
        help="RapidFuzz WRatio minimum for fuzzy TM hits (0-100, default: 92).",
    )
    translation_group.add_argument(
        "--tm-semantic-min-similarity",
        type=float,
        default=0.90,
        help="Minimum cosine similarity for semantic TM (default: 0.90).",
    )
    translation_group.add_argument(
        "--tm-project-id",
        default="",
        help="Optional project id for TM scope=project/global clustering.",
    )
    translation_group.add_argument(
        "--tm-embedding-model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="SentenceTransformer model id when --tm-mode=semantic.",
    )
    translation_group.add_argument(
        "--tm-import",
        dest="tm_import_path",
        default=None,
        metavar="PATH",
        help="NDJSON file to import into TM before translating.",
    )
    translation_group.add_argument(
        "--tm-export",
        dest="tm_export_path",
        default=None,
        metavar="PATH",
        help="Write TM NDJSON after each file (if PATH is a directory, uses <stem>.tm.ndjson).",
    )
    translation_group.add_argument(
        "--no-dual",
        action="store_true",
        help="Do not output bilingual PDF files",
    )
    translation_group.add_argument(
        "--no-mono",
        action="store_true",
        help="Do not output monolingual PDF files",
    )
    translation_group.add_argument(
        "--formular-font-pattern",
        help="Font pattern to identify formula text",
    )
    translation_group.add_argument(
        "--formular-char-pattern",
        help="Character pattern to identify formula text",
    )
    translation_group.add_argument(
        "--split-short-lines",
        action="store_true",
        help="Force split short lines into different paragraphs (may cause poor typesetting & bugs)",
    )
    translation_group.add_argument(
        "--short-line-split-factor",
        type=float,
        default=0.8,
        help="Split threshold factor. The actual threshold is the median length of all lines on the current page * this factor",
    )
    translation_group.add_argument(
        "--skip-clean",
        action="store_true",
        help="Skip PDF cleaning step",
    )
    translation_group.add_argument(
        "--dual-translate-first",
        action="store_true",
        help="Put translated pages first in dual PDF mode",
    )
    translation_group.add_argument(
        "--disable-rich-text-translate",
        action="store_true",
        help="Disable rich text translation (may help improve compatibility with some PDFs)",
    )
    translation_group.add_argument(
        "--use-alternating-pages-dual",
        action="store_true",
        help="Use alternating pages mode for dual PDF. When enabled, original and translated pages are arranged in alternate order.",
    )
    translation_group.add_argument(
        "--watermark-output-mode",
        "--watermark-mode",
        type=str,
        choices=["watermarked", "no_watermark", "both"],
        default="watermarked",
        help="Watermark output mode.",
    )
    translation_group.add_argument(
        "--max-pages-per-part",
        "--split-pages",
        type=int,
        dest="max_pages_per_part",
        default=None,
        help="Maximum number of pages per part for split translation.",
    )
    translation_group.add_argument(
        "--report-interval",
        type=float,
        default=0.1,
        help="Progress report interval in seconds (default: 0.1)",
    )
    translation_group.add_argument(
        "--translate-table-text",
        action="store_true",
        default=False,
        help="Translate table text (experimental)",
    )
    translation_group.add_argument(
        "--ocr-mode",
        type=str,
        choices=["off", "auto", "force", "hybrid"],
        default="off",
        help=(
            "OCR/layout fallback: off (default), auto (scanned or very low extracted text), "
            "force (OCR all translatable pages within --ocr-pages if set), "
            "hybrid (merge OCR boxes that do not overlap native text)."
        ),
    )
    translation_group.add_argument(
        "--ocr-pages",
        type=str,
        default=None,
        help=(
            "Restrict OCR to these original-document pages (same syntax as --pages). "
            "If omitted with --ocr-mode=force, all translatable pages are OCR'd."
        ),
    )
    translation_group.add_argument(
        "--ocr-lang",
        type=str,
        default=None,
        help="Comma-separated OCR language hints (logged for future engine tuning; MVP uses RapidOCR defaults).",
    )
    translation_group.add_argument(
        "--ocr-debug",
        action="store_true",
        default=False,
        help="Write ocr_routing.json under the working directory (in addition to --debug IL dumps).",
    )
    translation_group.add_argument(
        "--show-char-box",
        action="store_true",
        default=False,
        help="Show character box (debug only)",
    )
    translation_group.add_argument(
        "--skip-scanned-detection",
        action="store_true",
        default=False,
        help="Skip scanned document detection (speeds up processing for non-scanned documents)",
    )
    translation_group.add_argument(
        "--ocr-workaround",
        action="store_true",
        default=False,
        help="Add text fill background (experimental)",
    )
    translation_group.add_argument(
        "--custom-system-prompt",
        help="Custom system prompt for translation.",
        default=None,
    )
    translation_group.add_argument(
        "--add-formula-placehold-hint",
        action="store_true",
        default=False,
        help="Add formula placeholder hint for translation. (Currently not recommended, it may affect translation quality, default: False)",
    )
    translation_group.add_argument(
        "--disable-same-text-fallback",
        action="store_true",
        default=False,
        help="Disable fallback translation when LLM output matches input text. (default: False)",
    )
    translation_group.add_argument(
        "--glossary-files",
        type=str,
        default=None,
        help="Comma-separated paths to glossary CSV files.",
    )
    translation_group.add_argument(
        "--pool-max-workers",
        type=int,
        help="Maximum number of worker threads for internal task processing pools. If not specified, defaults to QPS value. This parameter directly sets the worker count, replacing previous QPS-based dynamic calculations.",
    )
    translation_group.add_argument(
        "--term-pool-max-workers",
        type=int,
        help="Maximum number of worker threads dedicated to automatic term extraction. If not specified, defaults to --pool-max-workers (or QPS value when unset).",
    )
    translation_group.add_argument(
        "--no-auto-extract-glossary",
        action="store_false",
        dest="auto_extract_glossary",
        default=True,
        help="Disable automatic term extraction. (Config file: set auto_extract_glossary = false)",
    )
    translation_group.add_argument(
        "--auto-enable-ocr-workaround",
        action="store_true",
        default=False,
        help="Enable automatic OCR workaround. If a document is detected as heavily scanned, this will attempt to enable OCR processing and skip further scan detection. Note: This option interacts with `--ocr-workaround` and `--skip-scanned-detection`. See documentation for details. (default: False)",
    )
    translation_group.add_argument(
        "--primary-font-family",
        type=str,
        choices=["serif", "sans-serif", "script"],
        default=None,
        help="Override primary font family for translated text. Choices: 'serif' for serif fonts, 'sans-serif' for sans-serif fonts, 'script' for script/italic fonts. If not specified, uses automatic font selection based on original text properties.",
    )
    translation_group.add_argument(
        "--only-include-translated-page",
        action="store_true",
        default=False,
        help="Only include translated pages in the output PDF. Effective only when --pages is used.",
    )
    translation_group.add_argument(
        "--save-auto-extracted-glossary",
        action="store_true",
        default=False,
        help="Save automatically extracted glossary terms to a CSV file in the output directory.",
    )
    translation_group.add_argument(
        "--disable-graphic-element-process",
        action="store_true",
        default=False,
        help="Disable graphic element process. (default: False)",
    )
    translation_group.add_argument(
        "--no-merge-alternating-line-numbers",
        action="store_false",
        dest="merge_alternating_line_numbers",
        default=True,
        help="Disable post-processing that merges alternating line-number layouts (by default this feature is enabled).",
    )
    translation_group.add_argument(
        "--skip-translation",
        action="store_true",
        default=False,
        help="Skip translation step. (default: False)",
    )
    translation_group.add_argument(
        "--skip-form-render",
        action="store_true",
        default=False,
        help="Skip form rendering. (default: False)",
    )
    translation_group.add_argument(
        "--skip-curve-render",
        action="store_true",
        default=False,
        help="Skip curve rendering. (default: False)",
    )
    translation_group.add_argument(
        "--only-parse-generate-pdf",
        action="store_true",
        default=False,
        help="Only parse PDF and generate output PDF without translation (default: False). This skips all translation-related processing including layout analysis, paragraph finding, style processing, and translation itself.",
    )
    translation_group.add_argument(
        "--remove-non-formula-lines",
        action="store_true",
        default=False,
        help="Remove non-formula lines from paragraph areas. This removes decorative lines that are not part of formulas, while protecting lines in figure/table areas. (default: False)",
    )
    translation_group.add_argument(
        "--non-formula-line-iou-threshold",
        type=float,
        default=0.9,
        help="IoU threshold for detecting paragraph overlap when removing non-formula lines. Higher values are more conservative. (default: 0.9)",
    )
    translation_group.add_argument(
        "--figure-table-protection-threshold",
        type=float,
        default=0.9,
        help="IoU threshold for protecting lines in figure/table areas when removing non-formula lines. Higher values provide more protection. (default: 0.9)",
    )
    translation_group.add_argument(
        "--skip-formula-offset-calculation",
        action="store_true",
        default=False,
        help="Skip formula offset calculation (default: False)",
    )
    translation_group.add_argument(
        "--openai",
        action="store_true",
        help="Use OpenAI translator.",
    )
    service_group = parser.add_argument_group(
        "Translation - OpenAI Options",
        description="OpenAI specific options",
    )
    service_group.add_argument(
        "--openai-model",
        default="gpt-4o-mini",
        help="The OpenAI model to use for translation.",
    )
    service_group.add_argument(
        "--openai-base-url",
        help="The base URL for the OpenAI API.",
    )
    service_group.add_argument(
        "--openai-api-key",
        "-k",
        help="The API key for the OpenAI API.",
    )
    service_group.add_argument(
        "--openai-term-extraction-model",
        default=None,
        help="OpenAI model to use for automatic term extraction. Defaults to --openai-model when unset.",
    )
    service_group.add_argument(
        "--openai-term-extraction-base-url",
        default=None,
        help="Base URL for the OpenAI API used during automatic term extraction. Falls back to --openai-base-url when unset.",
    )
    service_group.add_argument(
        "--openai-term-extraction-api-key",
        default=None,
        help="API key for the OpenAI API used during automatic term extraction. Falls back to --openai-api-key when unset.",
    )
    service_group.add_argument(
        "--enable-json-mode-if-requested",
        action="store_true",
        default=False,
        help="Enable JSON mode for OpenAI requests.",
    )
    service_group.add_argument(
        "--send-dashscope-header",
        action="store_true",
        default=False,
        help="Send DashScope data inspection header to disable input/output inspection.",
    )
    service_group.add_argument(
        "--no-send-temperature",
        action="store_true",
        default=False,
        help="Do not send temperature parameter to OpenAI API (default: send temperature).",
    )
    service_group.add_argument(
        "--openai-reasoning",
        type=str,
        default=None,
        help="Reasoning string to send in the OpenAI request body 'reasoning' field. If not set, the field is not sent.",
    )
    service_group.add_argument(
        "--openai-term-extraction-reasoning",
        type=str,
        default=None,
        help="Reasoning string for the OpenAI term extraction translator. If not set, no reasoning field is sent for term extraction requests.",
    )
    translation_group.add_argument(
        "--translator",
        "--provider",
        choices=["openai", "router", "local"],
        default="openai",
        dest="translator",
        help="Translation backend: openai, router (multi-provider TOML), or local (Ollama / OpenAI-compatible server).",
    )
    translation_group.add_argument(
        "--routing-profile",
        default=None,
        help="Router mode: override profile name for paragraph translation (default from TOML).",
    )
    translation_group.add_argument(
        "--term-extraction-profile",
        "--term-profile",
        dest="term_extraction_profile",
        default=None,
        help="Router mode: override profile name for automatic term extraction (default from TOML).",
    )
    translation_group.add_argument(
        "--routing-strategy",
        choices=["failover", "round_robin", "least_loaded", "cost_aware"],
        default=None,
        help="Router mode: override routing strategy from config.",
    )
    translation_group.add_argument(
        "--metrics-output",
        choices=["log", "json", "both"],
        default=None,
        help="Router mode: where to emit per-provider metrics (default from TOML).",
    )
    translation_group.add_argument(
        "--metrics-json-path",
        "--metrics-file",
        dest="metrics_json_path",
        default=None,
        help="Router mode: write metrics JSON to this path (when metrics-output includes json).",
    )
    translation_group.add_argument(
        "--validate-translators",
        action="store_true",
        help="Validate router or local translator configuration and exit (no PDF input required).",
    )
    local_group = parser.add_argument_group(
        "Translation - Local mode",
        "Used with --translator local (Ollama, vLLM, llama-cpp-python server, or any OpenAI-compatible local URL).",
    )
    local_group.add_argument(
        "--local-backend",
        default=None,
        choices=[
            "ollama",
            "vllm",
            "llama-cpp",
            "openai-compatible",
        ],
        help="Local inference backend preset (default: ollama when unset).",
    )
    local_group.add_argument(
        "--local-model",
        default=None,
        help="Model id for paragraph translation (required unless set in TOML).",
    )
    local_group.add_argument(
        "--local-base-url",
        default=None,
        help="Base URL for OpenAI-compatible servers (e.g. http://127.0.0.1:8000/v1). For Ollama, optional (default http://127.0.0.1:11434).",
    )
    local_group.add_argument(
        "--local-term-model",
        default=None,
        help="Optional different model for automatic term extraction.",
    )
    local_group.add_argument(
        "--local-term-base-url",
        default=None,
        help="Optional separate base URL for term extraction (OpenAI-compatible).",
    )
    local_group.add_argument(
        "--local-api-key",
        default=None,
        help="Optional API key for OpenAI-compatible local servers (vLLM often uses EMPTY).",
    )
    local_group.add_argument(
        "--local-timeout-seconds",
        type=float,
        default=None,
        help="HTTP timeout for local LLM requests (default: 120).",
    )
    local_group.add_argument(
        "--local-max-retries",
        type=int,
        default=None,
        help="Retries passed to the HTTP client for local completions (default: 2).",
    )
    local_group.add_argument(
        "--local-context-window",
        type=int,
        default=None,
        help="Hint for max context (documentation / tuning; optional).",
    )
    local_group.add_argument(
        "--local-translation-batch-tokens",
        type=int,
        default=None,
        help="Flush a paragraph batch when estimated tokens exceed this (default: 200).",
    )
    local_group.add_argument(
        "--local-translation-batch-paragraphs",
        type=int,
        default=None,
        help="Flush a paragraph batch when this many paragraphs accumulate (default: 5).",
    )
    local_group.add_argument(
        "--local-term-batch-tokens",
        type=int,
        default=None,
        help="Term extraction batch token threshold (default: 600).",
    )
    local_group.add_argument(
        "--local-term-batch-paragraphs",
        type=int,
        default=None,
        help="Term extraction batch paragraph threshold (default: 12).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Use debug logging level.",
    )
    parser.add_argument(
        "--rpc-doclayout",
        help="RPC service host address for document layout analysis",
    )
    parser.add_argument(
        "--rpc-doclayout2",
        help="RPC service host address for document layout analysis",
    )
    parser.add_argument(
        "--rpc-doclayout3",
        help="RPC service host address for document layout analysis",
    )
    parser.add_argument(
        "--rpc-doclayout4",
        help="RPC service host address for document layout analysis",
    )
    parser.add_argument(
        "--rpc-doclayout5",
        help="RPC service host address for document layout analysis",
    )
    parser.add_argument(
        "--rpc-doclayout6",
        help="RPC service host address for document layout analysis",
    )
    parser.add_argument(
        "--rpc-doclayout7",
        help="RPC service host address for document layout analysis",
    )
    parser.add_argument(
        "--working-dir",
        default=None,
        help="Working directory for translation. If not set, use temp directory.",
    )
    parser.add_argument(
        "--metadata-extra-data",
        default=None,
        help="Extra data for metadata",
    )
    parser.add_argument(
        "--enable-process-pool",
        action="store_true",
        help="DEBUG ONLY",
    )
    parser.add_argument(
        "translate_inputs",
        nargs="*",
        metavar="PDF",
        help="Input PDF file(s).",
    )
    return parser


def create_legacy_parser():
    """Deprecated name for tests; prefer :func:`build_translate_parent_parser`."""
    return build_translate_parent_parser()
