"""``doctranslate inspect`` — lightweight PDF introspection."""

from __future__ import annotations

import logging
from pathlib import Path

import pymupdf

from doctranslate.cli.exits import EXIT_OK
from doctranslate.cli.exits import EXIT_USAGE
from doctranslate.cli.output import OutputContext
from doctranslate.cli.project_config import load_flat_doctranslate_defaults

logger = logging.getLogger(__name__)


def run_inspect(ctx: OutputContext, paths: list[str], config: str | None) -> int:
    if not paths:
        ctx.emit_error("usage", "inspect requires at least one PDF path")
        return EXIT_USAGE
    merged = load_flat_doctranslate_defaults(Path(config)) if config else {}
    out: list[dict] = []
    for p in paths:
        fp = Path(p)
        if not fp.is_file():
            ctx.emit_error("not_found", str(fp))
            return EXIT_USAGE
        try:
            doc = pymupdf.open(fp)
            try:
                n = doc.page_count
            finally:
                doc.close()
        except Exception as e:
            ctx.emit_error("open_failed", str(e), {"path": str(fp)})
            return EXIT_USAGE
        out.append({"path": str(fp.resolve()), "page_count": n})
    if ctx.is_json():
        ctx.emit_result(True, {"files": out, "config_defaults": merged})
    else:
        for item in out:
            logger.info("%s: %s pages", item["path"], item["page_count"])
    return EXIT_OK
