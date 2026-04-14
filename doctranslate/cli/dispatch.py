"""Route between vNext subcommands and legacy flat CLI."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from doctranslate import __version__
from doctranslate.cli import assets_cmd
from doctranslate.cli import config_cmd
from doctranslate.cli import debug_cmd
from doctranslate.cli import glossary_cmd
from doctranslate.cli import inspect_cmd
from doctranslate.cli import tm_cmd
from doctranslate.cli.exits import EXIT_OK
from doctranslate.cli.exits import EXIT_USAGE
from doctranslate.cli.legacy_parser import create_legacy_parser
from doctranslate.cli.output import OutputContext
from doctranslate.cli.project_config import load_flat_doctranslate_defaults
from doctranslate.cli.project_config import load_profile_overlay
from doctranslate.cli.translate_run import run_legacy_translate_pipeline
from doctranslate.cli.vnext_argv import build_translate_legacy_argv
from doctranslate.cli.vnext_argv import build_translate_parent_parser

logger = logging.getLogger(__name__)

VNEXT_COMMANDS = frozenset(
    {
        "translate",
        "inspect",
        "glossary",
        "tm",
        "assets",
        "debug",
        "config",
        "help",
    },
)

LEGACY_TRIGGERS = frozenset(
    {
        "--warmup",
        "--files",
        "--generate-offline-assets",
        "--restore-offline-assets",
        "--validate-translators",
        "--openai",
        "--translator",
        "--rpc-doclayout",
        "--rpc-doclayout2",
        "--rpc-doclayout3",
        "--rpc-doclayout4",
        "--rpc-doclayout5",
        "--rpc-doclayout6",
        "--rpc-doclayout7",
    },
)


def _flag_base(tok: str) -> str:
    if "=" in tok:
        return tok.split("=", 1)[0]
    return tok


def should_use_vnext(argv: Sequence[str]) -> bool:
    """Use vNext router unless argv clearly targets legacy flat flags."""
    if not argv:
        return True
    i = 0
    while i < len(argv):
        t = argv[i]
        if t in ("-c", "--config"):
            i += 2
            continue
        if t.startswith("--config="):
            i += 1
            continue
        if t in VNEXT_COMMANDS:
            return True
        break
    for tok in argv:
        b = _flag_base(tok)
        if b in LEGACY_TRIGGERS:
            return False
    return True


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
        description="DocTranslater — PDF translation CLI (vNext).",
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
        description="Additional legacy flags may follow recognized options "
        "(passed through to the legacy parser).",
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


async def run_vnext_async(argv: Sequence[str]) -> int:
    parser = build_vnext_parser()
    args, unknown = parser.parse_known_args(list(argv))
    ctx = OutputContext(
        format=args.output_format,
        command=args.command or "help",
    )

    if unknown and getattr(args, "command", None) != "translate":
        parser.error(f"unrecognized arguments: {' '.join(unknown)}")

    if not args.command:
        parser.print_help()
        ctx.emit_result(
            True, {"hint": "Subcommands: translate, assets, config, inspect, ..."}
        )
        return EXIT_OK

    if args.command == "translate":
        args.extra_legacy = unknown
        effective_cfg = args.translate_config or args.global_config
        if effective_cfg:
            flat = load_flat_doctranslate_defaults(Path(effective_cfg))
            prof = load_profile_overlay(Path(effective_cfg), args.profile or "")
            flat.update(prof)
            for k, v in flat.items():
                if hasattr(args, k) and getattr(args, k) is None:
                    setattr(args, k, v)
        legacy = create_legacy_parser()
        if args.global_config and not args.translate_config:
            gflat = load_flat_doctranslate_defaults(Path(args.global_config))
            gprof = load_profile_overlay(Path(args.global_config), args.profile or "")
            gflat.update(gprof)
            known_dests = {
                getattr(a, "dest", None)
                for a in legacy._actions
                if getattr(a, "dest", None) not in (None, argparse.SUPPRESS)
            }
            legacy.set_defaults(
                **{k: v for k, v in gflat.items() if k in known_dests},
            )
        legacy_argv = build_translate_legacy_argv(args)
        l_ns = legacy.parse_args(legacy_argv)
        if args.provider == "openai":
            l_ns.openai_implicit = True
        if not l_ns.files:
            ctx.emit_error(
                "usage",
                "translate requires at least one PDF (positional paths).",
            )
            return EXIT_USAGE
        await run_legacy_translate_pipeline(legacy, l_ns)
        ctx.emit_result(True, {"status": "translate_finished"})
        return EXIT_OK

    if unknown:
        parser.error(f"unrecognized arguments: {' '.join(unknown)}")

    if args.command == "inspect":
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
        if args.tm_cmd == "import":
            return tm_cmd.cmd_import(ctx, args.ndjson, args.lang_in, args.lang_out)
        if args.tm_cmd == "export":
            return tm_cmd.cmd_export(ctx, args.out_path)
        if args.tm_cmd == "stats":
            return tm_cmd.cmd_stats(ctx)
        if args.tm_cmd == "purge":
            return tm_cmd.cmd_purge(ctx, yes=args.yes)

    if args.command == "assets":
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
    argv = list(sys.argv[1:] if argv is None else argv)
    if not should_use_vnext(argv):
        logger.warning(
            "Legacy flat CLI is deprecated; prefer `doctranslate translate ...`. "
            "See docs/migration.md.",
        )
        return asyncio.run(_run_legacy_main_async())

    return run_vnext(argv)


async def _run_legacy_main_async() -> int:
    legacy = create_legacy_parser()
    ns = legacy.parse_args()
    await run_legacy_translate_pipeline(legacy, ns)
    return EXIT_OK
