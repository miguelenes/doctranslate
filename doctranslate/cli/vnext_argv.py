"""Translate subcommand arguments (vNext) + argv mapping to legacy parser."""

from __future__ import annotations

import argparse
from typing import Any


def build_translate_parent_parser() -> argparse.ArgumentParser:
    """Flags and positionals merged into the root parser via ``parents=``."""
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument(
        "translate_inputs",
        nargs="*",
        metavar="PDF",
        help="Input PDF file(s).",
    )
    p.add_argument(
        "--provider",
        choices=["openai", "router", "local"],
        default=None,
        help="Translation backend (OpenAI no longer needs legacy --openai).",
    )
    p.add_argument(
        "--source-lang",
        "--lang-in",
        dest="lang_in",
        default=None,
        help="Source language code.",
    )
    p.add_argument(
        "--target-lang",
        "--lang-out",
        dest="lang_out",
        default=None,
        help="Target language code.",
    )
    p.add_argument(
        "--output-dir",
        "-o",
        dest="output_dir",
        default=None,
        help="Output directory.",
    )
    p.add_argument(
        "--request-rate",
        "--qps",
        dest="qps",
        type=int,
        default=None,
        help="Client-side request rate limit (legacy: --qps).",
    )
    p.add_argument(
        "-c",
        "--config",
        dest="translate_config",
        default=None,
        help="TOML config path.",
    )
    p.add_argument("--pages", "-p", default=None, help="Page ranges to translate.")
    p.add_argument(
        "--split-pages",
        dest="max_pages_per_part",
        type=int,
        default=None,
        help="Max pages per split part (legacy: --max-pages-per-part).",
    )
    p.add_argument(
        "--watermark-mode",
        dest="watermark_output_mode",
        choices=["watermarked", "no_watermark", "both"],
        default=None,
        help="Watermark output (legacy: --watermark-output-mode).",
    )
    p.add_argument("--routing-profile", default=None)
    p.add_argument("--term-profile", dest="term_extraction_profile", default=None)
    p.add_argument("--metrics-file", dest="metrics_json_path", default=None)
    p.add_argument("--metrics-output", default=None, choices=["log", "json", "both"])
    p.add_argument(
        "--routing-strategy",
        default=None,
        choices=["failover", "round_robin", "least_loaded", "cost_aware"],
    )
    p.add_argument("--ignore-cache", action="store_true")
    p.add_argument("--debug", action="store_true")
    p.add_argument("--working-dir", default=None)
    p.add_argument("--min-text-length", type=int, default=None)
    p.add_argument(
        "--tm-mode",
        choices=["off", "exact", "fuzzy", "semantic"],
        default=None,
    )
    p.add_argument(
        "--tm-scope",
        choices=["document", "project", "global"],
        default=None,
    )
    p.add_argument("--tm-import", dest="tm_import_path", default=None)
    p.add_argument("--tm-export", dest="tm_export_path", default=None)
    p.add_argument("--glossary-files", default=None)
    p.add_argument("--openai-model", default=None)
    p.add_argument("--openai-base-url", default=None)
    p.add_argument("--openai-api-key", "-k", default=None)
    p.add_argument("--local-model", default=None)
    p.add_argument("--local-backend", default=None)
    p.add_argument("--local-base-url", default=None)
    return p


def build_translate_legacy_argv(ns: Any) -> list[str]:
    """Build argv fragment consumable by ``create_legacy_parser().parse_args``."""
    out: list[str] = []

    def add_pair(name: str, value: Any) -> None:
        if value is None:
            return
        if isinstance(value, bool):
            if value:
                out.append(name)
            return
        out.extend([name, str(value)])

    for pdf in getattr(ns, "translate_inputs", None) or []:
        out.extend(["--files", str(pdf)])

    prov = getattr(ns, "provider", None)
    if prov:
        out.extend(["--translator", prov])

    add_pair("--lang-in", getattr(ns, "lang_in", None))
    add_pair("--lang-out", getattr(ns, "lang_out", None))
    add_pair("--output", getattr(ns, "output_dir", None))
    add_pair("--qps", getattr(ns, "qps", None))
    cfg = getattr(ns, "translate_config", None) or getattr(ns, "global_config", None)
    add_pair("--config", cfg)
    add_pair("--pages", getattr(ns, "pages", None))
    add_pair("--max-pages-per-part", getattr(ns, "max_pages_per_part", None))
    add_pair("--watermark-output-mode", getattr(ns, "watermark_output_mode", None))
    add_pair("--routing-profile", getattr(ns, "routing_profile", None))
    add_pair("--term-extraction-profile", getattr(ns, "term_extraction_profile", None))
    add_pair("--metrics-json-path", getattr(ns, "metrics_json_path", None))
    add_pair("--metrics-output", getattr(ns, "metrics_output", None))
    add_pair("--routing-strategy", getattr(ns, "routing_strategy", None))
    add_pair("--working-dir", getattr(ns, "working_dir", None))
    add_pair("--min-text-length", getattr(ns, "min_text_length", None))
    add_pair("--tm-mode", getattr(ns, "tm_mode", None))
    add_pair("--tm-scope", getattr(ns, "tm_scope", None))
    add_pair("--tm-import", getattr(ns, "tm_import_path", None))
    add_pair("--tm-export", getattr(ns, "tm_export_path", None))
    add_pair("--glossary-files", getattr(ns, "glossary_files", None))
    add_pair("--openai-model", getattr(ns, "openai_model", None))
    add_pair("--openai-base-url", getattr(ns, "openai_base_url", None))
    add_pair("--openai-api-key", getattr(ns, "openai_api_key", None))
    add_pair("--local-model", getattr(ns, "local_model", None))
    add_pair("--local-backend", getattr(ns, "local_backend", None))
    add_pair("--local-base-url", getattr(ns, "local_base_url", None))

    if getattr(ns, "ignore_cache", False):
        out.append("--ignore-cache")
    if getattr(ns, "debug", False):
        out.append("--debug")

    out.extend(getattr(ns, "extra_legacy", []) or [])
    return out
