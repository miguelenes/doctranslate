"""``doctranslate config`` subcommands."""

from __future__ import annotations

import logging
from pathlib import Path

from doctranslate.cli.exits import EXIT_OK
from doctranslate.cli.exits import EXIT_USAGE
from doctranslate.cli.exits import EXIT_VALIDATION
from doctranslate.cli.output import OutputContext
from doctranslate.translator.config import load_nested_translator_config
from doctranslate.translator.config import merge_cli_router_overrides_from_mapping
from doctranslate.translator.config import validate_router_config
from doctranslate.translator.local_config import (
    convert_local_translator_to_router_nested,
)
from doctranslate.translator.local_config import local_cli_dict_from_args
from doctranslate.translator.local_config import merge_local_cli_into_nested
from doctranslate.translator.local_config import validate_local_nested
from doctranslate.translator.providers.local_preflight import LocalPreflightError
from doctranslate.translator.providers.local_preflight import run_local_preflight

logger = logging.getLogger(__name__)


def _cli_router_override_dict_from_ns(ns: object) -> dict:
    out: dict = {}
    if getattr(ns, "routing_profile", None):
        out["routing_profile"] = ns.routing_profile
    if getattr(ns, "term_extraction_profile", None):
        out["term_extraction_profile"] = ns.term_extraction_profile
    if getattr(ns, "routing_strategy", None):
        out["routing_strategy"] = ns.routing_strategy
    if getattr(ns, "metrics_output", None):
        out["metrics_output"] = ns.metrics_output
    if getattr(ns, "metrics_json_path", None):
        out["metrics_json_path"] = ns.metrics_json_path
    return out


def cmd_validate(ctx: OutputContext, ns: object) -> int:
    mode = getattr(ns, "translator", None) or "router"
    if mode == "router":
        cfg = getattr(ns, "config", None)
        if not cfg:
            ctx.emit_error("usage", "Router validation requires --config PATH")
            return EXIT_USAGE
        nested = load_nested_translator_config(Path(cfg))
        nested = merge_cli_router_overrides_from_mapping(
            nested,
            _cli_router_override_dict_from_ns(ns),
        )
        validate_router_config(nested)
        logger.info("Router translator configuration is valid.")
        ctx.emit_result(True, {"translator": "router"})
        return EXIT_OK
    if mode == "local":
        nested = load_nested_translator_config(
            Path(ns.config) if getattr(ns, "config", None) else None,
        )
        nested = merge_local_cli_into_nested(nested, local_cli_dict_from_args(ns))
        nested = nested.model_copy(update={"translator": "local"})
        err = validate_local_nested(nested)
        if err:
            ctx.emit_error("validation_failed", err)
            return EXIT_VALIDATION
        try:
            run_local_preflight(nested)
        except LocalPreflightError as e:
            ctx.emit_error("validation_failed", str(e))
            return EXIT_VALIDATION
        converted = convert_local_translator_to_router_nested(nested)
        validate_router_config(converted)
        logger.info("Local translator configuration is valid and preflight succeeded.")
        ctx.emit_result(True, {"translator": "local"})
        return EXIT_OK
    ctx.emit_error("usage", "config validate requires --translator router|local")
    return EXIT_USAGE


def cmd_init(ctx: OutputContext, dest: str | None) -> int:
    path = Path(dest or "doctranslate.toml")
    if path.exists():
        ctx.emit_error("exists", f"Refusing to overwrite existing file: {path}")
        return EXIT_USAGE
    sample = (
        '[doctranslate]\ntranslator = "router"\nlang_in = "en"\nlang_out = "zh"\n'
        "# Add [doctranslate.providers.x] and [doctranslate.profiles.y] per docs.\n"
    )
    path.write_text(sample, encoding="utf-8")
    logger.info("Wrote sample config to %s", path)
    ctx.emit_result(True, {"path": str(path)})
    return EXIT_OK


def cmd_show(ctx: OutputContext, path: str | None) -> int:
    p = Path(path or "doctranslate.toml")
    if not p.is_file():
        ctx.emit_error("not_found", str(p))
        return EXIT_USAGE
    text = p.read_text(encoding="utf-8")
    if ctx.is_json():
        ctx.emit_result(True, {"path": str(p), "content": text})
    else:
        print(text, end="" if text.endswith("\n") else "\n")
    return EXIT_OK
