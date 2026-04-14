"""Regression guard for IL OCR routing density helper (pure IL, no RapidOCR)."""

from __future__ import annotations

import pytest
from doctranslate.format.pdf.document_il import il_version_1
from doctranslate.format.pdf.document_il.midend.ocr_merge import (
    text_density_chars_per_sqpt,
)
from doctranslate.format.pdf.document_il.utils.style_helper import BLACK

pytestmark = pytest.mark.requires_pdf


def _char(x0, y0, x1, y1, u="a"):
    st = il_version_1.PdfStyle(font_id="base", font_size=10.0, graphic_state=BLACK)
    b = il_version_1.Box(x=x0, y=y0, x2=x1, y2=y1)
    vb = il_version_1.VisualBbox(box=il_version_1.Box(x0, y0, x1, y1))
    return il_version_1.PdfCharacter(
        box=b,
        pdf_character_id=1,
        advance=1.0,
        char_unicode=u,
        vertical=False,
        pdf_style=st,
        xobj_id=0,
        visual_bbox=vb,
        render_order=None,
        sub_render_order=0,
    )


def _page():
    return il_version_1.Page(
        mediabox=il_version_1.Mediabox(box=il_version_1.Box(0, 0, 100, 100)),
        cropbox=il_version_1.Cropbox(box=il_version_1.Box(0, 0, 100, 100)),
        page_number=0,
    )


def test_text_density_single_printable_char():
    p = _page()
    p.pdf_character = [_char(0, 0, 10, 10, "x")]
    # cropbox 100x100 => area 10_000 sq pt; one counted char => 1e-4
    assert text_density_chars_per_sqpt(p) == pytest.approx(1.0 / 10_000.0)


def test_text_density_ignores_whitespace_and_cid():
    p = _page()
    p.pdf_character = [
        _char(0, 0, 1, 1, " "),
        _char(1, 0, 2, 1, "\n"),
        _char(2, 0, 3, 1, "(cid:12)"),
        _char(3, 0, 4, 1, "z"),
    ]
    assert text_density_chars_per_sqpt(p) == pytest.approx(1.0 / 10_000.0)
