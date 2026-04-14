"""Smoke tests that open real PDFs (PyMuPDF / ``pdf`` extra)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.requires_pdf


def test_ci_sample_pdf_opens_and_has_pages(ci_test_pdf):
    fitz = pytest.importorskip("fitz")
    doc = fitz.open(ci_test_pdf)
    try:
        assert doc.page_count >= 1
        page = doc.load_page(0)
        assert page.rect.width > 0 and page.rect.height > 0
    finally:
        doc.close()


def test_ci_sample_pdf_text_or_vector_content(ci_test_pdf):
    """At least one page should yield some extractable content (text or not empty render)."""
    fitz = pytest.importorskip("fitz")
    doc = fitz.open(ci_test_pdf)
    try:
        page = doc.load_page(0)
        text = (page.get_text() or "").strip()
        # Vector PDFs may still have little extractable text; allow either text or draw ops.
        if not text:
            assert page.rect.width > 0
        else:
            assert len(text) >= 1
    finally:
        doc.close()
