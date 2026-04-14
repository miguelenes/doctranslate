"""``doctranslate assets`` subcommands."""

from __future__ import annotations

import logging
from pathlib import Path

import doctranslate.assets.assets
from doctranslate.cli.exits import EXIT_OK
from doctranslate.cli.exits import EXIT_USAGE
from doctranslate.cli.output import OutputContext

logger = logging.getLogger(__name__)


def cmd_warmup(ctx: OutputContext) -> int:
    doctranslate.assets.assets.warmup()
    logger.info("Warmup completed.")
    ctx.emit_result(True, {"status": "warmup_complete"})
    return EXIT_OK


def cmd_pack_offline(ctx: OutputContext, dest: str) -> int:
    if not dest:
        ctx.emit_error("usage", "pack-offline requires a destination directory")
        return EXIT_USAGE
    doctranslate.assets.assets.generate_offline_assets_package(Path(dest))
    logger.info("Offline assets package generated at %s", dest)
    ctx.emit_result(True, {"path": dest})
    return EXIT_OK


def cmd_restore_offline(ctx: OutputContext, src: str) -> int:
    if not src:
        ctx.emit_error("usage", "restore-offline requires a package path")
        return EXIT_USAGE
    doctranslate.assets.assets.restore_offline_assets_package(Path(src))
    logger.info("Offline assets restored from %s", src)
    ctx.emit_result(True, {"path": src})
    return EXIT_OK
