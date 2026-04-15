"""PDF pipeline micro-benchmark using ``only_parse_generate_pdf`` (no LLM, minimal stages)."""

from __future__ import annotations

from pathlib import Path

import pytest
from doctranslate.docvision.doclayout import DocLayoutModel
from doctranslate.format.pdf.high_level import translate
from doctranslate.format.pdf.translation_config import TranslationConfig
from doctranslate.format.pdf.translation_settings import TranslationSettings
from doctranslate.translator.translator import BaseTranslator
from doctranslate.translator.types import TranslatorCapabilities

pytestmark = [
    pytest.mark.perf,
    pytest.mark.requires_pdf,
    pytest.mark.requires_full,
]


class _StubTranslator(BaseTranslator):
    """Minimal translator; unused for parse-only runs but required by ``TranslationConfig``."""

    name = "perf_stub"
    model = "stub"

    @property
    def translator_capabilities(self) -> TranslatorCapabilities:
        return TranslatorCapabilities(
            supports_llm=True,
            supports_json_mode=True,
            supports_reasoning=False,
            supports_streaming=False,
            max_output_tokens=1024,
            provider_id=self.name,
        )

    def do_llm_translate(self, text, rate_limit_params=None):
        return text

    def do_translate(self, text, rate_limit_params=None):
        return text


@pytest.mark.perf
def test_perf_translate_only_parse_generate_pdf(
    benchmark,
    tmp_path: Path,
    ci_test_pdf: Path,
):
    """One pipeline run with parse-only stages (see ``TRANSLATE_STAGES`` pruning)."""
    out_dir = tmp_path / "out"
    work_root = tmp_path / "work"
    out_dir.mkdir()
    work_root.mkdir()
    translator = _StubTranslator("en", "zh", ignore_cache=True)
    settings = TranslationSettings(
        lang_in="en",
        lang_out="zh",
        output_dir=out_dir,
        working_dir=work_root,
        only_parse_generate_pdf=True,
        skip_scanned_detection=True,
        auto_extract_glossary=False,
        use_rich_pbar=False,
    )
    doc_layout_model = DocLayoutModel.load_available()
    config = TranslationConfig(
        translator,
        ci_test_pdf,
        doc_layout_model,
        settings,
        term_extraction_translator=translator,
    )

    def _run():
        return translate(config)

    result = benchmark.pedantic(_run, rounds=1, iterations=1)
    assert result is not None
    assert (
        result.mono_watermarked_pdf
        or result.dual_watermarked_pdf
        or result.mono_plain_pdf
        or result.dual_plain_pdf
    )
