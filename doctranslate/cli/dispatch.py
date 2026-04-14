"""DocTranslater CLI: subcommands and ``translate`` entry."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from doctranslate import __version__
from doctranslate.cli import debug_cmd
from doctranslate.cli import glossary_cmd
from doctranslate.cli.exits import EXIT_OK
from doctranslate.cli.exits import EXIT_USAGE
from doctranslate.cli.output import OutputContext
from doctranslate.cli.project_config import load_flat_doctranslate_defaults
from doctranslate.cli.project_config import load_profile_overlay
from doctranslate.cli.translate_cli import build_translate_parent_parser

logger = logging.getLogger(__name__)


def _register_local_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument("--local-backend", default=None)
    p.add_argument("--local-model", default=None)
    p.add_argument("--local-base-url", default=None)
    p.add_argument("--local-term-model", default=None)
    p.add_argument("--local-term-base-url", default=None)
    p.add_argument("--local-api-key", default=None)
    p.add_argument("--local-timeout-seconds", type=float, default=None)
    p.add_argument("--local-max-retries", type=int, default=None)
    p.add_argument("--local-context-window", type=int, default=None)
    p.add_argument("--local-translation-batch-tokens", type=int, default=None)
    p.add_argument("--local-translation-batch-paragraphs", type=int, default=None)
    p.add_argument("--local-term-batch-tokens", type=int, default=None)
    p.add_argument("--local-term-batch-paragraphs", type=int, default=None)


def build_vnext_parser() -> argparse.ArgumentParser:
    translate_parent = build_translate_parent_parser()
    root = argparse.ArgumentParser(
        prog="doctranslate",
        description="DocTranslater — PDF translation CLI.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    root.add_argument(
        "--output-format",
        choices=["human", "json"],
        default="human",
        help="Structured JSON output for scripting.",
    )
    root.add_argument(
        "--profile",
        default=None,
        help="Optional named profile overlay from the TOML config file.",
    )
    root.add_argument(
        "-c",
        "--config",
        dest="global_config",
        default=None,
        help="Default TOML merged into translate when translate omits -c.",
    )
    root.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    sub = root.add_subparsers(dest="command", required=False)
    sub.add_parser(
        "translate",
        parents=[translate_parent],
        help="Translate PDF(s) through the IL pipeline.",
    )

    insp = sub.add_parser("inspect", help="Inspect PDFs without translating.")
    insp.add_argument("pdf_paths", nargs="+", metavar="PDF")
    insp.add_argument("-c", "--config", dest="inspect_config", default=None)

    gloss = sub.add_parser("glossary", help="Glossary utilities.")
    gs = gloss.add_subparsers(dest="gloss_cmd", required=True)
    gv = gs.add_parser("validate", help="Validate glossary CSV files.")
    gv.add_argument("csv_paths", nargs="+", metavar="CSV")
    gv.add_argument(
        "--target-lang",
        default="zh",
        help="Target language column to read (same as --lang-out).",
    )

    tm = sub.add_parser("tm", help="Translation memory utilities.")
    ts = tm.add_subparsers(dest="tm_cmd", required=True)
    ti = ts.add_parser("import", help="Import TM NDJSON into the local SQLite cache.")
    ti.add_argument("ndjson", metavar="PATH")
    ti.add_argument("--lang-in", default="en")
    ti.add_argument("--lang-out", default="zh")
    te = ts.add_parser("export", help="Export all TM rows to NDJSON.")
    te.add_argument("out_path", metavar="PATH")
    tst = ts.add_parser("stats", help="Count TM rows.")
    tp = ts.add_parser("purge", help="Delete all TM rows (requires --yes).")
    tp.add_argument("--yes", action="store_true")
    ts.add_parser(
        "migrate-v1-cache",
        help="Import legacy ~/.cache/doctranslate/cache.v1.db into TM (one-time).",
    )

    ast = sub.add_parser("assets", help="Model/asset cache management.")
    a_s = ast.add_subparsers(dest="asset_cmd", required=True)
    a_s.add_parser("warmup", help="Download and verify required assets.")
    ap = a_s.add_parser("pack-offline", help="Write offline asset bundle.")
    ap.add_argument("dest", metavar="DIR")
    ar = a_s.add_parser("restore-offline", help="Restore offline asset bundle.")
    ar.add_argument("src", metavar="PATH")

    dbg = sub.add_parser("debug", help="Internal diagnostics (interface may change).")
    d_s = dbg.add_subparsers(dest="debug_cmd", required=True)
    d_s.add_parser("info", help="Print runtime information.")

    srv = sub.add_parser(
        "serve",
        help="Run the HTTP API server (install DocTranslater[api]).",
    )
    srv.add_argument(
        "--host",
        default="0.0.0.0",  # noqa: S104
        help="Bind address (use 127.0.0.1 for local-only).",
    )
    srv.add_argument("--port", type=int, default=8000, help="Listen port.")
    srv.add_argument(
        "--reload",
        action="store_true",
        help="Development auto-reload (do not use in production).",
    )

    cfg = sub.add_parser("config", help="Project configuration utilities.")
    c_s = cfg.add_subparsers(dest="cfg_cmd", required=True)
    cv = c_s.add_parser(
        "validate", help="Validate router/local translator configuration."
    )
    cv.add_argument(
        "--translator",
        choices=["router", "local"],
        required=True,
    )
    cv.add_argument("-c", "--config", dest="config", default=None)
    cv.add_argument("--routing-profile", default=None)
    cv.add_argument("--term-extraction-profile", default=None)
    cv.add_argument("--routing-strategy", default=None)
    cv.add_argument("--metrics-output", default=None, choices=["log", "json", "both"])
    cv.add_argument("--metrics-json-path", default=None)
    _register_local_flags(cv)

    ci = c_s.add_parser("init", help="Write a sample doctranslate.toml.")
    ci.add_argument(
        "path",
        nargs="?",
        default="doctranslate.toml",
        metavar="FILE",
    )
    cs = c_s.add_parser("show", help="Print a TOML config file.")
    cs.add_argument(
        "path",
        nargs="?",
        default="doctranslate.toml",
        metavar="FILE",
    )

    return root


def _cli_output_format(args: argparse.Namespace) -> str:
    """Resolve JSON vs human for the current subcommand."""
    if getattr(args, "command", None) == "translate":
        sub = getattr(args, "translate_output_format", None)
        if sub is not None:
            return sub
    return getattr(args, "output_format", "human")


async def run_vnext_async(argv: Sequence[str]) -> int:
    parser = build_vnext_parser()
    args = parser.parse_args(list(argv))
    ctx = OutputContext(
        format=_cli_output_format(args),
        command=args.command or "help",
    )

    if not args.command:
        parser.print_help()
        ctx.emit_result(
            True,
            {
                "hint": ("Subcommands: translate, assets, config, inspect, serve, ..."),
            },
        )
        return EXIT_OK

    if args.command == "serve":
        from doctranslate.http_api.serve import run_serve

        run_serve(host=args.host, port=args.port, reload=args.reload)
        return EXIT_OK

    if args.command == "translate":
        from doctranslate.bootstrap import ensure_user_cache_dirs
        from doctranslate.cli.translate_run import run_legacy_translate_pipeline

        ensure_user_cache_dirs()
        tpl = build_translate_parent_parser()
        known_dests = {
            getattr(a, "dest", None)
            for a in tpl._actions
            if getattr(a, "dest", None) not in (None, argparse.SUPPRESS)
        }
        if args.global_config:
            gflat = load_flat_doctranslate_defaults(Path(args.global_config))
            gprof = load_profile_overlay(Path(args.global_config), args.profile or "")
            gflat.update(gprof)
            for k, v in gflat.items():
                if k in known_dests and hasattr(args, k) and getattr(args, k) is None:
                    setattr(args, k, v)
        args.config = args.global_config
        args.files = list(args.translate_inputs or [])
        args.openai_implicit = args.translator == "openai" and not args.openai
        if (
            not args.files
            and not args.validate_translators
            and not getattr(args, "request_json", None)
        ):
            ctx.emit_error(
                "usage",
                "translate requires at least one PDF (positional paths) or "
                "--request-json.",
            )
            return EXIT_USAGE
        payload = await run_legacy_translate_pipeline(parser, args)
        out: dict = {"status": "translate_finished"}
        if isinstance(payload, dict):
            out.update(payload)
        ctx.emit_result(True, out)
        return EXIT_OK

    if args.command == "inspect":
        from doctranslate.bootstrap import ensure_user_cache_dirs
        from doctranslate.cli import inspect_cmd

        ensure_user_cache_dirs()
        return inspect_cmd.run_inspect(
            ctx,
            list(args.pdf_paths),
            args.inspect_config,
        )

    if args.command == "glossary":
        if args.gloss_cmd == "validate":
            return glossary_cmd.cmd_validate(
                ctx,
                list(args.csv_paths),
                args.target_lang,
            )

    if args.command == "tm":
        from doctranslate.bootstrap import ensure_user_cache_dirs
        from doctranslate.cli import tm_cmd

        ensure_user_cache_dirs()
        if args.tm_cmd == "import":
            return tm_cmd.cmd_import(ctx, args.ndjson, args.lang_in, args.lang_out)
        if args.tm_cmd == "export":
            return tm_cmd.cmd_export(ctx, args.out_path)
        if args.tm_cmd == "stats":
            return tm_cmd.cmd_stats(ctx)
        if args.tm_cmd == "purge":
            return tm_cmd.cmd_purge(ctx, yes=args.yes)
        if args.tm_cmd == "migrate-v1-cache":
            return tm_cmd.cmd_migrate_v1_cache(ctx)

    if args.command == "assets":
        from doctranslate.bootstrap import ensure_user_cache_dirs
        from doctranslate.cli import assets_cmd

        ensure_user_cache_dirs()
        if args.asset_cmd == "warmup":
            return assets_cmd.cmd_warmup(ctx)
        if args.asset_cmd == "pack-offline":
            return assets_cmd.cmd_pack_offline(ctx, args.dest)
        if args.asset_cmd == "restore-offline":
            return assets_cmd.cmd_restore_offline(ctx, args.src)

    if args.command == "debug":
        if args.debug_cmd == "info":
            return debug_cmd.cmd_info(ctx)

    if args.command == "config":
        from doctranslate.cli import config_cmd

        if args.cfg_cmd == "validate":
            return config_cmd.cmd_validate(ctx, args)
        if args.cfg_cmd == "init":
            return config_cmd.cmd_init(ctx, args.path)
        if args.cfg_cmd == "show":
            return config_cmd.cmd_show(ctx, args.path)

    ctx.emit_error("unknown_command", str(args.command))
    return EXIT_USAGE


def run_vnext(argv: Sequence[str]) -> int:
    try:
        return asyncio.run(run_vnext_async(argv))
    except SystemExit as e:
        code = e.code
        if code is None:
            return EXIT_OK
        return int(code) if isinstance(code, int) else EXIT_USAGE


def main_dispatch(argv: Sequence[str] | None = None) -> int:
    """Entry from ``cli()`` after logging is configured."""
    return run_vnext(list(sys.argv[1:] if argv is None else argv))
