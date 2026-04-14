"""Tests for OCR page-range parsing and global page helpers."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from doctranslate.format.pdf.translation_config import TranslationConfig
from doctranslate.format.pdf.translation_settings import TranslationSettings

pytestmark = pytest.mark.requires_pdf


def _minimal_pdf(tmp_path: Path) -> Path:
    p = tmp_path / "x.pdf"
    p.write_bytes(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    return p


@pytest.fixture()
def mock_translator():
    t = MagicMock()
    t.cache = None
    return t


def test_ocr_pages_parsed_and_filters_global(tmp_path, mock_translator):
    pdf = _minimal_pdf(tmp_path)
    cfg = TranslationConfig(
        mock_translator,
        pdf,
        object(),
        TranslationSettings(
            lang_in="en",
            lang_out="zh",
            output_dir=str(tmp_path),
            working_dir=str(tmp_path),
            pages=None,
            ocr_mode="force",
            ocr_pages="2,4-5",
        ),
    )
    assert cfg.ocr_page_ranges == [(2, 2), (4, 5)]
    assert cfg.ocr_pages_allow_global(2) is True
    assert cfg.ocr_pages_allow_global(3) is False


def test_global_page_1based_with_split_offset(tmp_path, mock_translator):
    pdf = _minimal_pdf(tmp_path)
    cfg = TranslationConfig(
        mock_translator,
        pdf,
        object(),
        TranslationSettings(
            lang_in="en",
            lang_out="zh",
            output_dir=str(tmp_path),
            working_dir=str(tmp_path),
            split_part_origin_offset=10,
        ),
    )
    assert cfg.global_page_1based(0) == 11
    assert cfg.global_page_1based(2) == 13


def test_should_translate_global_respects_original_ranges(tmp_path, mock_translator):
    pdf = _minimal_pdf(tmp_path)
    cfg = TranslationConfig(
        mock_translator,
        pdf,
        object(),
        TranslationSettings(
            lang_in="en",
            lang_out="zh",
            output_dir=str(tmp_path),
            working_dir=str(tmp_path),
            pages="1-2",
        ),
    )
    assert cfg.should_translate_global_page(1) is True
    assert cfg.should_translate_global_page(3) is False
