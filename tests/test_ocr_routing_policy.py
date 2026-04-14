"""Routing policy tests (no OCR engine)."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from doctranslate.format.pdf.document_il import il_version_1
from doctranslate.format.pdf.document_il.midend.ocr_routing import OcrRouting
from doctranslate.format.pdf.translation_config import TranslationConfig


def _minimal_pdf(tmp_path: Path) -> Path:
    p = tmp_path / "x.pdf"
    p.write_bytes(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    return p


@pytest.fixture()
def mock_translator():
    t = MagicMock()
    t.cache = None
    return t


def _page(page_number: int = 0):
    return il_version_1.Page(
        mediabox=il_version_1.Mediabox(box=il_version_1.Box(0, 0, 200, 200)),
        cropbox=il_version_1.Cropbox(box=il_version_1.Box(0, 0, 200, 200)),
        page_number=page_number,
    )


def test_route_force(tmp_path, mock_translator):
    pdf = _minimal_pdf(tmp_path)
    cfg = TranslationConfig(
        mock_translator,
        pdf,
        "en",
        "zh",
        doc_layout_model=object(),
        output_dir=str(tmp_path),
        working_dir=str(tmp_path),
        ocr_mode="force",
    )
    r = OcrRouting(cfg)
    route, sig = r._route_for_page(_page(0))
    assert route == "ocr_first"
    assert sig["global_page_1based"] == 1


def test_route_auto_when_scanned_map_true(tmp_path, mock_translator):
    pdf = _minimal_pdf(tmp_path)
    cfg = TranslationConfig(
        mock_translator,
        pdf,
        "en",
        "zh",
        doc_layout_model=object(),
        output_dir=str(tmp_path),
        working_dir=str(tmp_path),
        ocr_mode="auto",
    )
    cfg.shared_context_cross_split_part.page_scan_is_scanned[0] = True
    r = OcrRouting(cfg)
    route, _ = r._route_for_page(_page(0))
    assert route == "ocr_first"


def test_route_auto_native_when_dense_text(tmp_path, mock_translator):
    pdf = _minimal_pdf(tmp_path)
    cfg = TranslationConfig(
        mock_translator,
        pdf,
        "en",
        "zh",
        doc_layout_model=object(),
        output_dir=str(tmp_path),
        working_dir=str(tmp_path),
        ocr_mode="auto",
        ocr_low_text_density_threshold=1e-9,
    )
    cfg.shared_context_cross_split_part.page_scan_is_scanned[0] = False
    page = _page(0)
    st = il_version_1.PdfStyle(
        font_id="base",
        font_size=10.0,
        graphic_state=il_version_1.GraphicState(
            passthrough_per_char_instruction="0 g 0 G",
        ),
    )
    b = il_version_1.Box(0, 0, 1, 1)
    vb = il_version_1.VisualBbox(box=il_version_1.Box(0, 0, 1, 1))
    # Many letters to push density above default threshold
    page.pdf_character = [
        il_version_1.PdfCharacter(
            box=b,
            pdf_character_id=i,
            advance=1.0,
            char_unicode="x",
            vertical=False,
            pdf_style=st,
            xobj_id=0,
            visual_bbox=vb,
            render_order=None,
            sub_render_order=0,
        )
        for i in range(500)
    ]
    r = OcrRouting(cfg)
    route, _ = r._route_for_page(page)
    assert route == "native"


def test_route_hybrid_label(tmp_path, mock_translator):
    pdf = _minimal_pdf(tmp_path)
    cfg = TranslationConfig(
        mock_translator,
        pdf,
        "en",
        "zh",
        doc_layout_model=object(),
        output_dir=str(tmp_path),
        working_dir=str(tmp_path),
        ocr_mode="hybrid",
    )
    cfg.shared_context_cross_split_part.page_scan_is_scanned[0] = True
    r = OcrRouting(cfg)
    route, _ = r._route_for_page(_page(0))
    assert route == "hybrid"
