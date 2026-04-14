"""``doctranslate glossary`` subcommands."""

from __future__ import annotations

import logging
from pathlib import Path

from doctranslate.cli.exits import EXIT_OK
from doctranslate.cli.exits import EXIT_USAGE
from doctranslate.cli.exits import EXIT_VALIDATION
from doctranslate.cli.output import OutputContext
from doctranslate.glossary import Glossary

logger = logging.getLogger(__name__)


def cmd_validate(ctx: OutputContext, paths: list[str], target_lang: str) -> int:
    if not paths:
        ctx.emit_error("usage", "glossary validate requires CSV path(s)")
        return EXIT_USAGE
    results = []
    for p in paths:
        fp = Path(p)
        if not fp.is_file():
            ctx.emit_error("not_found", str(fp))
            return EXIT_USAGE
        try:
            g = Glossary.from_csv(fp, target_lang)
            results.append(
                {
                    "path": str(fp),
                    "name": g.name,
                    "entries": len(g.entries),
                },
            )
        except Exception as e:
            ctx.emit_error("invalid_csv", str(e), {"path": str(fp)})
            return EXIT_VALIDATION
    ctx.emit_result(True, {"glossaries": results})
    if not ctx.is_json():
        for r in results:
            logger.info("OK %s (%s entries)", r["path"], r["entries"])
    return EXIT_OK
