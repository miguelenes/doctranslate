"""``doctranslate tm`` — translation memory file operations."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from doctranslate.cli.exits import EXIT_OK
from doctranslate.cli.exits import EXIT_USAGE
from doctranslate.cli.exits import EXIT_VALIDATION
from doctranslate.cli.output import OutputContext
from doctranslate.translator.cache import TranslationCache
from doctranslate.translator.tm_policy import TMMode
from doctranslate.translator.tm_policy import TMRuntimeConfig
from doctranslate.translator.tm_policy import TMScope

logger = logging.getLogger(__name__)


def _cache_for_cli(lang_in: str, lang_out: str) -> TranslationCache:
    c = TranslationCache(
        "doctranslate-cli",
        {"lang_in": lang_in, "lang_out": lang_out},
    )
    rt = TMRuntimeConfig(
        mode=TMMode.EXACT,
        scope=TMScope.GLOBAL,
    )
    c.configure_tm_runtime(
        tm_runtime=rt,
        document_scope="",
        project_scope="",
        glossary_signature="",
        glossary_pairs=[],
    )
    return c


def cmd_import(ctx: OutputContext, ndjson: str, lang_in: str, lang_out: str) -> int:
    if not ndjson:
        ctx.emit_error("usage", "tm import requires NDJSON path")
        return EXIT_USAGE
    p = Path(ndjson)
    if not p.is_file():
        ctx.emit_error("not_found", str(p))
        return EXIT_USAGE
    c = _cache_for_cli(lang_in, lang_out)
    try:
        n = c.import_tm_ndjson(p)
    except Exception as e:
        ctx.emit_error("import_failed", str(e))
        return EXIT_VALIDATION
    ctx.emit_result(True, {"imported": n, "path": str(p)})
    if not ctx.is_json():
        logger.info("Imported %s TM rows from %s", n, p)
    return EXIT_OK


def cmd_export(ctx: OutputContext, out_path: str) -> int:
    """Export **all** TM rows (full SQLite dump of the TM table)."""
    if not out_path:
        ctx.emit_error("usage", "tm export requires output path")
        return EXIT_USAGE
    from doctranslate.translator.cache import _TmEntry

    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    try:
        with outp.open("w", encoding="utf-8") as f:
            for row in _TmEntry.select():
                rec = {
                    "translate_engine": row.translate_engine,
                    "translate_engine_params": row.translate_engine_params,
                    "lang_in": row.lang_in,
                    "lang_out": row.lang_out,
                    "source_text_raw": row.source_text_raw,
                    "source_text_norm": row.source_text_norm,
                    "target_text": row.target_text,
                    "placeholder_signature": row.placeholder_signature,
                    "glossary_signature": row.glossary_signature,
                    "project_scope": row.project_scope,
                    "document_scope": row.document_scope,
                    "origin_mode": row.origin_mode,
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
    except Exception as e:
        ctx.emit_error("export_failed", str(e))
        return EXIT_VALIDATION
    ctx.emit_result(True, {"exported": n, "path": str(outp)})
    if not ctx.is_json():
        logger.info("Exported %s TM rows to %s", n, outp)
    return EXIT_OK


def cmd_stats(ctx: OutputContext) -> int:
    from doctranslate.translator.cache import _TmEntry

    try:
        n = _TmEntry.select().count()
    except Exception as e:
        ctx.emit_error("stats_failed", str(e))
        return EXIT_VALIDATION
    ctx.emit_result(True, {"tm_rows": n})
    if not ctx.is_json():
        logger.info("TM rows in database: %s", n)
    return EXIT_OK


def cmd_migrate_v1_cache(ctx: OutputContext) -> int:
    """Re-run one-time import of ``cache.v1.db`` into TM (clears migration marker first)."""
    from doctranslate.translator.cache import _run_legacy_migration_if_needed
    from doctranslate.translator.cache import _TmMigration
    from doctranslate.translator.cache import init_db

    init_db()
    try:
        _TmMigration.delete().where(
            _TmMigration.name == "legacy_cache_v1_import",
        ).execute()
    except Exception as e:
        ctx.emit_error("migrate_failed", str(e))
        return EXIT_VALIDATION
    try:
        _run_legacy_migration_if_needed()
    except Exception as e:
        ctx.emit_error("migrate_failed", str(e))
        return EXIT_VALIDATION
    ctx.emit_result(True, {"status": "legacy_v1_import_attempted"})
    if not ctx.is_json():
        logger.info(
            "Legacy cache.v1.db import attempted (see logs if file was absent)."
        )
    return EXIT_OK


def cmd_purge(ctx: OutputContext, *, yes: bool) -> int:
    """Delete all TM rows (keeps legacy exact cache table)."""
    if not yes:
        ctx.emit_error("usage", "tm purge requires --yes")
        return EXIT_USAGE
    from doctranslate.translator.cache import _TmEntry

    try:
        n = _TmEntry.delete().execute()
    except Exception as e:
        ctx.emit_error("purge_failed", str(e))
        return EXIT_VALIDATION
    ctx.emit_result(True, {"deleted_tm_rows": n})
    if not ctx.is_json():
        logger.info("Deleted %s TM rows", n)
    return EXIT_OK
