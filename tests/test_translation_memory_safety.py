"""TM safety: glossary and length gates."""

from doctranslate.translator.cache import TranslationCache
from doctranslate.translator.cache import clean_test_db
from doctranslate.translator.cache import init_test_db
from doctranslate.translator.tm_policy import TMMode
from doctranslate.translator.tm_policy import TMRuntimeConfig
from doctranslate.translator.tm_policy import TMScope


def test_short_segment_skips_fuzzy():
    test_db = init_test_db()
    try:
        c = TranslationCache("eng", {"lang_in": "en", "lang_out": "zh"})
        c.configure_tm_runtime(
            tm_runtime=TMRuntimeConfig(
                mode=TMMode.FUZZY,
                scope=TMScope.GLOBAL,
                min_segment_chars=20,
            ),
            document_scope="",
            project_scope="",
            glossary_signature="",
            glossary_pairs=[],
        )
        c.set("x" * 25, "y" * 25)
        r = c.lookup("short")
        assert r.translation is None
    finally:
        clean_test_db(test_db)


def test_glossary_mismatch_rejects_fuzzy():
    test_db = init_test_db()
    try:
        c = TranslationCache("eng", {"lang_in": "en", "lang_out": "zh"})
        c.configure_tm_runtime(
            tm_runtime=TMRuntimeConfig(mode=TMMode.FUZZY, scope=TMScope.GLOBAL),
            document_scope="",
            project_scope="",
            glossary_signature="ab12",
            glossary_pairs=[("OpenAI", "开放人工智能")],
        )
        c.set("Use OpenAI for tasks", "Use wrong vendor for tasks")
        c2 = TranslationCache("eng", {"lang_in": "en", "lang_out": "zh"})
        c2.configure_tm_runtime(
            tm_runtime=TMRuntimeConfig(mode=TMMode.FUZZY, scope=TMScope.GLOBAL),
            document_scope="",
            project_scope="",
            glossary_signature="ab12",
            glossary_pairs=[("OpenAI", "开放人工智能")],
        )
        r = c2.lookup("Use OpenAI for tasks!")  # fuzzy-close to stored source
        assert r.translation is None
    finally:
        clean_test_db(test_db)
