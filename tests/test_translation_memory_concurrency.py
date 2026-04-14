"""Concurrent TM writes (same pattern as legacy cache cleanup stress)."""

from concurrent.futures import ThreadPoolExecutor

from doctranslate.translator.cache import TranslationCache
from doctranslate.translator.cache import _TmEntry
from doctranslate.translator.cache import clean_test_db
from doctranslate.translator.cache import init_test_db
from doctranslate.translator.tm_policy import TMMode
from doctranslate.translator.tm_policy import TMRuntimeConfig
from doctranslate.translator.tm_policy import TMScope


def test_tm_concurrent_writes(monkeypatch):
    test_db = init_test_db()
    try:
        cache = TranslationCache("pool", {"lang_in": "en", "lang_out": "zh"})
        cache.configure_tm_runtime(
            tm_runtime=TMRuntimeConfig(
                mode=TMMode.EXACT,
                scope=TMScope.GLOBAL,
                cleanup_every_n_writes=1,
                max_tm_rows=80,
            ),
            document_scope="",
            project_scope="",
            glossary_signature="",
            glossary_pairs=[],
        )
        monkeypatch.setattr(
            "doctranslate.translator.cache.CLEAN_PROBABILITY",
            0.0,
        )

        def task(n):
            cache.set(f"k{n}", f"v{n}")

        with ThreadPoolExecutor(max_workers=8) as ex:
            ex.map(task, range(120))

        assert _TmEntry.select().count() <= 80
    finally:
        clean_test_db(test_db)
