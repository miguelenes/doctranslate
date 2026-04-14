"""Structured PDF translation options (replaces long TranslationConfig constructors)."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from doctranslate.format.pdf.split_manager import BaseSplitStrategy
    from doctranslate.glossary import Glossary
    from doctranslate.progress_monitor import ProgressMonitor


class WatermarkOutputMode(enum.Enum):
    Watermarked = "watermarked"
    NoWatermark = "no_watermark"
    Both = "both"


@dataclass
class TranslationSettings:
    """All translation job options except translator models and input path."""

    lang_in: str = "en"
    lang_out: str = "zh"
    pages: str | None = None
    output_dir: str | Path | None = None
    debug: bool = False
    working_dir: str | Path | None = None
    no_dual: bool = False
    no_mono: bool = False
    formular_font_pattern: str | None = None
    formular_char_pattern: str | None = None
    qps: int = 1
    split_short_lines: bool = False
    short_line_split_factor: float = 0.8
    use_rich_pbar: bool = True
    progress_monitor: ProgressMonitor | None = None
    skip_clean: bool = False
    dual_translate_first: bool = False
    disable_rich_text_translate: bool = False
    report_interval: float = 0.1
    min_text_length: int = 5
    use_alternating_pages_dual: bool = False
    watermark_output_mode: WatermarkOutputMode = WatermarkOutputMode.Watermarked
    split_strategy: BaseSplitStrategy | None = None
    table_model: object | None = None
    show_char_box: bool = False
    skip_scanned_detection: bool = False
    ocr_workaround: bool = False
    custom_system_prompt: str | None = None
    add_formula_placehold_hint: bool = False
    glossaries: list[Glossary] | None = None
    pool_max_workers: int | None = None
    auto_extract_glossary: bool = True
    auto_enable_ocr_workaround: bool = False
    primary_font_family: str | None = None
    only_include_translated_page: bool | None = False
    save_auto_extracted_glossary: bool = True
    enable_graphic_element_process: bool = True
    merge_alternating_line_numbers: bool = True
    skip_translation: bool = False
    skip_form_render: bool = False
    skip_curve_render: bool = False
    only_parse_generate_pdf: bool = False
    remove_non_formula_lines: bool = False
    non_formula_line_iou_threshold: float = 0.9
    figure_table_protection_threshold: float = 0.9
    skip_formula_offset_calculation: bool = False
    metadata_extra_data: str | None = None
    term_pool_max_workers: int | None = None
    disable_same_text_fallback: bool = False
    llm_translation_batch_max_tokens: int | None = None
    llm_translation_batch_max_paragraphs: int | None = None
    llm_term_extraction_batch_max_tokens: int | None = None
    llm_term_extraction_batch_max_paragraphs: int | None = None
    tm_mode: str = "off"
    tm_scope: str = "document"
    tm_min_segment_chars: int = 12
    tm_fuzzy_min_score: float = 92.0
    tm_semantic_min_similarity: float = 0.90
    tm_project_id: str = ""
    tm_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    tm_import_path: str | None = None
    tm_export_path: str | None = None
    ocr_mode: str = "off"
    ocr_pages: str | None = None
    ocr_lang_hints: list[str] = field(default_factory=list)
    ocr_debug_dump: bool = False
    ocr_scanned_ssim_threshold: float = 0.95
    ocr_low_text_density_threshold: float = 0.02
    split_part_origin_offset: int = 0
