"""Translation memory layered lookup (L1b normalized, fuzzy)."""

from doctranslate.translator.cache import TranslationCache
from doctranslate.translator.cache import _TmEntry
from doctranslate.translator.cache import _TranslationCache
from doctranslate.translator.cache import clean_test_db
from doctranslate.translator.cache import init_test_db
from doctranslate.translator.tm_policy import TMMode
from doctranslate.translator.tm_policy import TMRuntimeConfig
from doctranslate.translator.tm_policy import TMScope


def _cfg(
    cache: TranslationCache,
    *,
    mode: TMMode = TMMode.EXACT,
    doc: str = "doc1",
    pairs: list | None = None,
    gsig: str = "",
):
    cache.configure_tm_runtime(
        tm_runtime=TMRuntimeConfig(mode=mode, scope=TMScope.GLOBAL),
        document_scope=doc,
        project_scope="",
        glossary_signature=gsig,
        glossary_pairs=pairs or [],
    )


def test_legacy_exact_hit():
    test_db = init_test_db()
    try:
        c = TranslationCache("eng", {"lang_in": "en", "lang_out": "zh"})
        _cfg(c, mode=TMMode.FUZZY)
        c.set("alpha", "阿尔法")
        r = c.lookup("alpha")
        assert r.translation == "阿尔法"
        assert r.layer == "legacy_exact"
    finally:
        clean_test_db(test_db)


def test_normalized_hit_whitespace():
    test_db = init_test_db()
    try:
        c = TranslationCache("eng", {"lang_in": "en", "lang_out": "zh"})
        _cfg(c, mode=TMMode.EXACT)
        c.set("Hello   world", "你好世界")
        c2 = TranslationCache("eng", {"lang_in": "en", "lang_out": "zh"})
        _cfg(c2, mode=TMMode.EXACT)
        r = c2.lookup("Hello world")
        assert r.translation == "你好世界"
        assert r.layer == "normalized"
    finally:
        clean_test_db(test_db)


def test_fuzzy_hit_high_score():
    test_db = init_test_db()
    try:
        c = TranslationCache("eng", {"lang_in": "en", "lang_out": "zh"})
        _cfg(c, mode=TMMode.FUZZY)
        c.set("The quick brown fox", "敏捷的棕色狐狸")
        c2 = TranslationCache("eng", {"lang_in": "en", "lang_out": "zh"})
        _cfg(c2, mode=TMMode.FUZZY)
        r = c2.lookup("The quick brown fox!")  # tiny punctuation change
        assert r.translation == "敏捷的棕色狐狸"
        assert r.layer == "fuzzy"
    finally:
        clean_test_db(test_db)


def test_promote_to_legacy_exact():
    test_db = init_test_db()
    try:
        c = TranslationCache("eng", {"lang_in": "en", "lang_out": "zh"})
        _cfg(c, mode=TMMode.EXACT)
        c.set("foo   bar", "FOO")
        c2 = TranslationCache("eng", {"lang_in": "en", "lang_out": "zh"})
        _cfg(c2, mode=TMMode.EXACT)
        r = c2.lookup("foo bar")
        assert r.layer == "normalized"
        c2.promote_to_legacy_exact("foo bar", r.translation)
        hit = _TranslationCache.get_or_none(
            translate_engine="eng",
            translate_engine_params=c2.translate_engine_params,
            original_text="foo bar",
        )
        assert hit is not None
        assert hit.translation == "FOO"
    finally:
        clean_test_db(test_db)


def test_document_scope_miss():
    test_db = init_test_db()
    try:
        c = TranslationCache("eng", {"lang_in": "en", "lang_out": "zh"})
        c.configure_tm_runtime(
            tm_runtime=TMRuntimeConfig(mode=TMMode.EXACT, scope=TMScope.DOCUMENT),
            document_scope="docA",
            project_scope="",
            glossary_signature="",
            glossary_pairs=[],
        )
        c.set("only", "solo")
        # Drop legacy row so we exercise TM scope (legacy is not document-scoped).
        _TranslationCache.delete().execute()
        c2 = TranslationCache("eng", {"lang_in": "en", "lang_out": "zh"})
        c2.configure_tm_runtime(
            tm_runtime=TMRuntimeConfig(mode=TMMode.EXACT, scope=TMScope.DOCUMENT),
            document_scope="docB",
            project_scope="",
            glossary_signature="",
            glossary_pairs=[],
        )
        r = c2.lookup("only")
        assert r.translation is None
    finally:
        clean_test_db(test_db)


def test_tm_cleanup_trims_rows():
    test_db = init_test_db()
    try:
        c = TranslationCache("x", {"lang_in": "en", "lang_out": "zh"})
        c.configure_tm_runtime(
            tm_runtime=TMRuntimeConfig(
                mode=TMMode.EXACT,
                scope=TMScope.GLOBAL,
                cleanup_every_n_writes=1,
                max_tm_rows=5,
            ),
            document_scope="",
            project_scope="",
            glossary_signature="",
            glossary_pairs=[],
        )
        for i in range(12):
            c.set(f"key{i}", f"val{i}")
        assert _TmEntry.select().count() <= 5
    finally:
        clean_test_db(test_db)
