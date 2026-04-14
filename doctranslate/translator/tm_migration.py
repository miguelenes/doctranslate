"""One-time migration from legacy translation cache DB files into TM store."""

from __future__ import annotations

import contextlib
import json
import logging
from pathlib import Path

import peewee
from peewee import AutoField
from peewee import CharField
from peewee import Model
from peewee import SqliteDatabase
from peewee import TextField

from doctranslate.translator.tm_normalize import normalize_for_tm
from doctranslate.translator.tm_normalize import placeholder_signature
from doctranslate.translator.tm_normalize import stable_hash

logger = logging.getLogger(__name__)


class _LegacyRow(Model):
    id = AutoField()
    translate_engine = CharField(max_length=128)
    translate_engine_params = TextField()
    original_text = TextField()
    translation = TextField()

    class Meta:
        database = SqliteDatabase(None)
        table_name = "_translationcache"


def migrate_legacy_sqlite_into_tm(
    legacy_path: Path,
    tm_insert_fn,
) -> int:
    """Read rows from a legacy cache DB and insert via ``tm_insert_fn`` callable.

    ``tm_insert_fn`` signature:
        (engine, params_json, raw, norm, raw_h, norm_h, tgt, ph_sig, gloss_sig,
         project_scope, document_scope, origin_mode) -> None

    Returns number of rows processed (attempted).
    """
    if not legacy_path.is_file():
        logger.debug("TM migration: legacy file missing: %s", legacy_path)
        return 0

    ldb = SqliteDatabase(
        str(legacy_path),
        pragmas={"journal_mode": "wal", "busy_timeout": 3000},
    )
    ldb.bind([_LegacyRow], bind_refs=False, bind_backrefs=False)
    try:
        ldb.connect()

        tables = ldb.get_tables()
        if "_translationcache" not in tables:
            logger.info(
                "TM migration: no _translationcache table in %s",
                legacy_path,
            )
            return 0

        _LegacyRow._meta.database = ldb
        count = 0
        for row in _LegacyRow.select():
            raw = row.original_text
            params = row.translate_engine_params
            try:
                pobj = json.loads(params)
                lang_in = str(pobj.get("lang_in", ""))
            except Exception:
                lang_in = ""
            norm = normalize_for_tm(raw, lang_in=lang_in)
            raw_h = stable_hash(raw)
            norm_h = stable_hash(norm)
            ph = placeholder_signature(raw)
            tm_insert_fn(
                row.translate_engine,
                params,
                raw,
                norm,
                raw_h,
                norm_h,
                row.translation,
                ph,
                "",
                "",
                "",
                "legacy_import",
            )
            count += 1
        logger.info("TM migration: imported %s rows from %s", count, legacy_path)
        return count
    except peewee.OperationalError as e:
        logger.warning("TM migration failed for %s: %s", legacy_path, e)
        return 0
    finally:
        with contextlib.suppress(Exception):
            ldb.close()
