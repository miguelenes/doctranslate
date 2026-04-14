"""Contract tests for structured translation settings."""

from pathlib import Path
from unittest.mock import MagicMock

from doctranslate.format.pdf.translation_config import TranslationConfig
from doctranslate.format.pdf.translation_settings import TranslationSettings


def test_translation_config_from_default_settings(tmp_path: Path):
    tr = MagicMock()
    tr.cache = None
    cfg = TranslationConfig(
        tr,
        tmp_path / "in.pdf",
        object(),
        TranslationSettings(
            lang_in="en",
            lang_out="zh",
            output_dir=str(tmp_path),
            working_dir=str(tmp_path),
        ),
    )
    assert cfg.lang_in == "en"
    assert cfg.lang_out == "zh"
    assert cfg.skip_clean is False
    assert cfg.ocr_mode == "off"


def test_from_settings_classmethod(tmp_path: Path):
    tr = MagicMock()
    tr.cache = None
    s = TranslationSettings(pages="1-2")
    cfg = TranslationConfig.from_settings(
        tr,
        tmp_path / "x.pdf",
        object(),
        s,
    )
    assert cfg.page_ranges == [(1, 2)]
