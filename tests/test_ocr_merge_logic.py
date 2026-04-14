"""Unit tests for OCR merge helpers (no RapidOCR / no PDF)."""

from doctranslate.format.pdf.document_il import il_version_1
from doctranslate.format.pdf.document_il.midend.ocr_merge import merge_hybrid_native_ocr
from doctranslate.format.pdf.document_il.midend.ocr_merge import (
    replace_page_characters_with_ocr,
)
from doctranslate.format.pdf.document_il.midend.ocr_merge import (
    text_density_chars_per_sqpt,
)
from doctranslate.format.pdf.document_il.utils.style_helper import BLACK


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
    p = il_version_1.Page(
        mediabox=il_version_1.Mediabox(box=il_version_1.Box(0, 0, 100, 100)),
        cropbox=il_version_1.Cropbox(box=il_version_1.Box(0, 0, 100, 100)),
        page_number=0,
    )
    return p


def test_text_density_ignores_cid_and_whitespace():
    page = _page()
    page.pdf_character = [
        _char(0, 0, 1, 1, "(cid:12)"),
        _char(0, 0, 1, 1, " "),
        _char(0, 0, 1, 1, "x"),
    ]
    d = text_density_chars_per_sqpt(page)
    assert d == 1.0 / (100.0 * 100.0)


def test_replace_page_characters_with_ocr():
    page = _page()
    page.pdf_character = [_char(0, 0, 1, 1, "n")]
    ocr = [_char(10, 10, 20, 20, "O")]
    replace_page_characters_with_ocr(page, ocr)
    assert len(page.pdf_character) == 1
    assert page.pdf_character[0].char_unicode == "O"


def test_merge_hybrid_keeps_non_overlapping_ocr():
    page = _page()
    native = _char(0, 0, 10, 10, "n")
    page.pdf_character = [native]
    ocr_far = _char(50, 50, 60, 60, "O")
    merge_hybrid_native_ocr(page, [ocr_far], iou_replace_threshold=0.35)
    assert len(page.pdf_character) == 2
