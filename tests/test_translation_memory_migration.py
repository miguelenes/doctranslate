"""Import rows from a legacy cache.v1-style SQLite file into TM."""

from pathlib import Path

from doctranslate.translator.cache import _tm_insert_replace
from doctranslate.translator.cache import _TmEntry
from doctranslate.translator.cache import _TranslationCache
from doctranslate.translator.cache import clean_test_db
from doctranslate.translator.cache import init_test_db
from doctranslate.translator.tm_migration import migrate_legacy_sqlite_into_tm
from doctranslate.translator.tm_normalize import normalize_for_tm
from doctranslate.translator.tm_normalize import placeholder_signature
from doctranslate.translator.tm_normalize import stable_hash
from peewee import SqliteDatabase


def test_migrate_legacy_file(tmp_path: Path):
    test_db = init_test_db()
    try:
        v1 = tmp_path / "legacy.db"
        ldb = SqliteDatabase(str(v1))
        ldb.bind([_TranslationCache], bind_refs=False, bind_backrefs=False)
        ldb.connect()
        ldb.create_tables([_TranslationCache], safe=True)
        _TranslationCache.create(
            translate_engine="router",
            translate_engine_params='{"lang_in":"en","lang_out":"de"}',
            original_text="Hello",
            translation="Hallo",
        )
        ldb.close()

        def inserter(
            engine,
            params_json,
            raw,
            norm,
            raw_h,
            norm_h,
            tgt,
            ph_sig,
            gloss_sig,
            project_scope,
            document_scope,
            origin_mode,
        ):
            import time

            now = int(time.time() * 1000)
            li, lo = "en", "de"
            try:
                import json

                p = json.loads(params_json)
                li = str(p.get("lang_in", li))
                lo = str(p.get("lang_out", lo))
            except Exception:
                pass
            _tm_insert_replace(
                translate_engine=engine,
                translate_engine_params=params_json,
                lang_in=li,
                lang_out=lo,
                source_text_raw=raw,
                source_text_norm=norm,
                target_text=tgt,
                source_hash_raw=raw_h,
                source_hash_norm=norm_h,
                placeholder_signature=(ph_sig or "")[:64],
                glossary_signature=(gloss_sig or "")[:64],
                project_scope=(project_scope or "")[:512],
                document_scope=(document_scope or "")[:512],
                origin_mode=(origin_mode or "import")[:32],
                hit_count=0,
                last_used_at=now,
                created_at=now,
                embedding=None,
            )

        n = migrate_legacy_sqlite_into_tm(v1, inserter)
        assert n == 1
        row = _TmEntry.get_or_none(
            translate_engine="router",
            source_text_raw="Hello",
        )
        assert row is not None
        assert row.target_text == "Hallo"
        assert row.source_text_norm == normalize_for_tm("Hello", lang_in="en")
        assert row.source_hash_raw == stable_hash("Hello")
        assert row.placeholder_signature[:10] == placeholder_signature("Hello")[:10]
    finally:
        clean_test_db(test_db)
