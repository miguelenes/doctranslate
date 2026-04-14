"""Install profile smoke tests (minimal vs full dependency sets)."""


def test_minimal_schemas_import() -> None:
    """``doctranslate.schemas`` must import with only base project dependencies."""
    import doctranslate.schemas as sch

    assert sch.NestedTranslatorConfig is not None


def test_public_api_import() -> None:
    """Stable API re-exports (requires ``DocTranslater[full]`` in CI)."""
    import doctranslate.api as api

    assert callable(api.translate)
    assert callable(api.build_translators)
