"""Contract tests for ``doctranslate.api``."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.requires_full

import doctranslate.api as api  # noqa: E402


def test_public_api_all_exports() -> None:
    expected = set(api.__all__)
    assert expected.issuperset(
        {
            "PUBLIC_SCHEMA_VERSION",
            "TranslateResult",
            "TranslationConfig",
            "TranslationRequest",
            "TranslationResult",
            "TranslatorBuildResult",
            "async_translate",
            "build_translators",
            "inspect_input",
            "resolve_openai_api_key",
            "translate",
            "validate_request",
        },
    )
    for name in api.__all__:
        assert hasattr(api, name), f"missing export: {name}"


def test_validate_request_minimal_dict() -> None:
    req = api.validate_request(
        {
            "input_pdf": "/nonexistent/path/does-not-need-to-exist-for-validation.pdf",
            "lang_in": "en",
            "lang_out": "de",
            "translator": {"mode": "openai", "openai": {"model": "gpt-4o-mini"}},
        },
    )
    assert req.lang_out == "de"
    assert req.translator.mode.value == "openai"


def test_public_schema_version_constant() -> None:
    assert api.PUBLIC_SCHEMA_VERSION == "1"
