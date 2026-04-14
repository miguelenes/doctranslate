"""``doctranslate debug`` — internal diagnostics (unstable interface)."""

from __future__ import annotations

import logging
import platform
import sys

from doctranslate import __version__
from doctranslate.cli.exits import EXIT_OK
from doctranslate.cli.output import OutputContext

logger = logging.getLogger(__name__)


def cmd_info(ctx: OutputContext) -> int:
    info = {
        "version": __version__,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
    }
    ctx.emit_result(True, info)
    if not ctx.is_json():
        for k, v in info.items():
            logger.info("%s: %s", k, v)
    return EXIT_OK
