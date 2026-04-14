"""Install profile smoke tests (minimal vs full dependency sets)."""

from pathlib import Path

import pytest


def test_minimal_schemas_import() -> None:
    """``doctranslate.schemas`` must import with only base project dependencies."""
    import doctranslate.schemas as sch

    assert sch.NestedTranslatorConfig is not None


@pytest.mark.requires_full
def test_public_api_import() -> None:
    """Stable API re-exports (requires ``DocTranslater[full]`` in CI)."""
    import doctranslate.api as api

    assert callable(api.translate)
    assert callable(api.build_translators)
    assert callable(api.async_translate)
    assert callable(api.validate_request)
    assert callable(api.inspect_input)


def test_minimal_schemas_translation_request() -> None:
    """``TranslationRequest`` must import on the minimal dependency profile."""
    from doctranslate.schemas import TranslationRequest

    r = TranslationRequest.model_validate(
        {
            "input_pdf": "doc.pdf",
            "lang_in": "en",
            "lang_out": "zh",
            "translator": {"mode": "openai"},
        },
    )
    assert r.input_pdf == "doc.pdf"


@pytest.mark.requires_pdf
def test_pdf_stack_opens_ci_fixture() -> None:
    """``pdf`` extra only: open tracked CI PDF with PyMuPDF."""
    fitz = pytest.importorskip("fitz")
    root = Path(__file__).resolve().parents[1]
    pdf = root / "examples" / "ci" / "test.pdf"
    if not pdf.is_file():
        pytest.skip(f"Missing {pdf}")
    doc = fitz.open(pdf)
    try:
        assert doc.page_count >= 1
    finally:
        doc.close()
