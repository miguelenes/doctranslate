from __future__ import annotations

import hashlib
import logging
import shutil
import tempfile
import threading
from collections import Counter
from pathlib import Path

from doctranslate.const import CACHE_FOLDER
from doctranslate.format.pdf.split_manager import PageCountStrategy
from doctranslate.format.pdf.translation_settings import TranslationSettings
from doctranslate.glossary import Glossary
from doctranslate.glossary import GlossaryEntry
from doctranslate.translator.cache import flatten_glossary_entries_from_config
from doctranslate.translator.cache import glossary_signature_from_pairs
from doctranslate.translator.tm_policy import TMRuntimeConfig
from doctranslate.translator.translator import BaseTranslator

logger = logging.getLogger(__name__)


class SharedContextCrossSplitPart:
    def __init__(self):
        self.first_paragraph = None
        self.recent_title_paragraph = None
        self._lock = threading.Lock()
        self.user_glossaries: list[Glossary] = []
        self.auto_extracted_glossary: Glossary | None = None
        self.raw_extracted_terms: list[tuple[str, str]] = []
        self.auto_enabled_ocr_workaround = False
        # Per original-document page index (0-based): SSIM from scanned detection (part 0).
        self.page_scan_ssim: dict[int, float] = {}
        self.page_scan_is_scanned: dict[int, bool] = {}
        # Statistics for valid characters/text across the whole file
        self.valid_char_count_total: int = 0
        self.total_valid_text_token_count: int = 0

    def initialize_glossaries(self, initial_glossaries: list[Glossary] | None):
        with self._lock:
            self.user_glossaries = (
                list(initial_glossaries) if initial_glossaries else []
            )
            self.auto_extracted_glossary = None
            self.raw_extracted_terms = []
            self.unique_name = self._generate_unique_auto_glossary_name()
            self.norm_terms = set()
            for g in self.user_glossaries:
                for entity in g.normalized_lookup:
                    self.norm_terms.add(entity)
            # reset statistics buffer when initializing
            self.valid_char_count_total = 0
            self.total_valid_text_token_count = 0

    def add_raw_extracted_term_pair(self, src: str, tgt: str):
        with self._lock:
            self.raw_extracted_terms.append((src, tgt))

    def _generate_unique_auto_glossary_name(self) -> str:
        base_name = "auto_extracted_glossary"
        current_name = base_name
        suffix = 0
        existing_names = {g.name for g in self.user_glossaries}
        if (
            self.auto_extracted_glossary
            and self.auto_extracted_glossary.name == current_name
        ):
            pass

        while current_name in existing_names:
            suffix += 1
            current_name = f"{base_name}#{suffix}"
        return current_name

    def contains_term(self, term: str) -> bool:
        with self._lock:
            try:
                return term in self.norm_terms
            except Exception:
                return False

    def finalize_auto_extracted_glossary(self):
        with self._lock:
            self.auto_extracted_glossary = None

            if not self.raw_extracted_terms:
                self.raw_extracted_terms = []
                return

            term_translations: dict[str, list[str]] = {}
            for src, tgt in self.raw_extracted_terms:
                term_translations.setdefault(src, []).append(tgt)

            final_entries: list[GlossaryEntry] = []
            for src, tgts in term_translations.items():
                if not tgts:
                    continue
                most_common_tgt = Counter(tgts).most_common(1)[0][0]
                final_entries.append(GlossaryEntry(src, most_common_tgt))

            if final_entries:
                self.auto_extracted_glossary = Glossary(
                    name=self.unique_name, entries=final_entries
                )

    def get_glossaries(self) -> list[Glossary]:
        with self._lock:
            all_glossaries = list(self.user_glossaries)
            if self.auto_extracted_glossary:
                all_glossaries.append(self.auto_extracted_glossary)
            return all_glossaries

    def get_glossaries_for_translation(
        self, auto_extract_enabled: bool
    ) -> list[Glossary]:
        with self._lock:
            if auto_extract_enabled and self.auto_extracted_glossary:
                return [self.auto_extracted_glossary]
            else:
                all_glossaries = list(self.user_glossaries)
                if self.auto_extracted_glossary:
                    all_glossaries.append(self.auto_extracted_glossary)
                return all_glossaries

    def add_valid_counts(self, char_count: int, token_count: int):
        """Accumulate valid character and token counts in a threadsafe way."""
        if char_count <= 0 and token_count <= 0:
            return
        with self._lock:
            if char_count > 0:
                self.valid_char_count_total += char_count
            if token_count > 0:
                self.total_valid_text_token_count += token_count


class TranslationConfig:
    @staticmethod
    def create_max_pages_per_part_split_strategy(max_pages_per_part: int):
        return PageCountStrategy(max_pages_per_part)

    @classmethod
    def from_settings(
        cls,
        translator: BaseTranslator,
        input_file: str | Path,
        doc_layout_model,
        settings: TranslationSettings,
        *,
        term_extraction_translator: BaseTranslator | None = None,
    ) -> TranslationConfig:
        """Build a :class:`TranslationConfig` from structured settings."""
        return cls(
            translator,
            input_file,
            doc_layout_model,
            settings,
            term_extraction_translator=term_extraction_translator,
        )

    def __init__(
        self,
        translator: BaseTranslator,
        input_file: str | Path,
        doc_layout_model,
        settings: TranslationSettings,
        *,
        term_extraction_translator: BaseTranslator | None = None,
    ) -> None:
        s = settings
        self.translator = translator
        self.term_extraction_translator = term_extraction_translator or translator
        initial_user_glossaries = list(s.glossaries) if s.glossaries else []

        self.input_file = input_file
        self.lang_in = s.lang_in
        self.lang_out = s.lang_out
        self.font = None

        self.pages = s.pages
        self.page_ranges = self.parse_pages(s.pages) if s.pages else None
        self.debug = s.debug
        self.watermark_output_mode = s.watermark_output_mode

        working_dir = s.working_dir
        self.no_dual = s.no_dual
        self.no_mono = s.no_mono

        self.formular_font_pattern = s.formular_font_pattern
        self.formular_char_pattern = s.formular_char_pattern
        self.qps = s.qps
        self.pool_max_workers = (
            s.pool_max_workers if s.pool_max_workers is not None else s.qps
        )
        self.term_pool_max_workers = (
            s.term_pool_max_workers
            if s.term_pool_max_workers is not None
            else self.pool_max_workers
        )
        self.split_short_lines = s.split_short_lines

        self.short_line_split_factor = s.short_line_split_factor
        self.use_rich_pbar = s.use_rich_pbar
        self.progress_monitor = s.progress_monitor
        self.doc_layout_model = doc_layout_model

        self.skip_clean = s.skip_clean
        self.skip_scanned_detection = s.skip_scanned_detection

        self.dual_translate_first = s.dual_translate_first
        self.disable_rich_text_translate = s.disable_rich_text_translate

        self.report_interval = s.report_interval
        self.min_text_length = s.min_text_length
        self.use_alternating_pages_dual = s.use_alternating_pages_dual
        self.ocr_workaround = s.ocr_workaround
        self.merge_alternating_line_numbers = s.merge_alternating_line_numbers

        if self.ocr_workaround:
            self.skip_scanned_detection = True
            self.disable_rich_text_translate = True

        if s.progress_monitor and s.progress_monitor.cancel_event is None:
            s.progress_monitor.cancel_event = threading.Event()

        if working_dir is None:
            if s.debug:
                working_dir = Path(CACHE_FOLDER) / "working" / Path(input_file).stem
                self._is_temp_dir = False
            else:
                working_dir = tempfile.mkdtemp()
                self._is_temp_dir = True
        else:
            working_dir = Path(working_dir) / Path(input_file).stem
            self._is_temp_dir = False

        self.working_dir = working_dir

        Path(working_dir).mkdir(parents=True, exist_ok=True)

        output_dir = s.output_dir
        if output_dir is None:
            output_dir = Path.cwd()
        self.output_dir = output_dir

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        if not doc_layout_model:
            from doctranslate.docvision.doclayout import DocLayoutModel

            doc_layout_model = DocLayoutModel.load_available()
        self.doc_layout_model = doc_layout_model

        self.shared_context_cross_split_part = SharedContextCrossSplitPart()
        self.shared_context_cross_split_part.initialize_glossaries(
            initial_user_glossaries
        )

        self.split_strategy = s.split_strategy

        self._part_working_dirs: dict[int, Path] = {}
        self._part_output_dirs: dict[int, Path] = {}

        self.table_model = s.table_model
        self.show_char_box = s.show_char_box
        self.custom_system_prompt = s.custom_system_prompt
        self.add_formula_placehold_hint = s.add_formula_placehold_hint
        self.auto_extract_glossary = s.auto_extract_glossary
        self.auto_enable_ocr_workaround = s.auto_enable_ocr_workaround
        self.skip_translation = s.skip_translation
        self.only_parse_generate_pdf = s.only_parse_generate_pdf

        if self.skip_translation or self.only_parse_generate_pdf:
            self.auto_extract_glossary = False

        if s.auto_enable_ocr_workaround:
            self.ocr_workaround = False
            self.skip_scanned_detection = False

        assert s.primary_font_family in [
            None,
            "serif",
            "sans-serif",
            "script",
        ]
        self.primary_font_family = s.primary_font_family

        oitp = s.only_include_translated_page
        if oitp is None:
            oitp = False

        self.only_include_translated_page = oitp

        self.save_auto_extracted_glossary = s.save_auto_extracted_glossary

        self.table_model = None
        self.enable_graphic_element_process = s.enable_graphic_element_process
        self.skip_form_render = s.skip_form_render
        self.skip_curve_render = s.skip_curve_render
        self.remove_non_formula_lines = s.remove_non_formula_lines
        self.non_formula_line_iou_threshold = s.non_formula_line_iou_threshold
        self.figure_table_protection_threshold = s.figure_table_protection_threshold
        self.skip_formula_offset_calculation = s.skip_formula_offset_calculation

        self.metadata_extra_data = s.metadata_extra_data

        self.term_extraction_token_usage: dict[str, int] = {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "cache_hit_prompt_tokens": 0,
        }
        self.disable_same_text_fallback = s.disable_same_text_fallback

        self.llm_translation_batch_max_tokens = (
            s.llm_translation_batch_max_tokens
            if s.llm_translation_batch_max_tokens is not None
            else 200
        )
        self.llm_translation_batch_max_paragraphs = (
            s.llm_translation_batch_max_paragraphs
            if s.llm_translation_batch_max_paragraphs is not None
            else 5
        )
        self.llm_term_extraction_batch_max_tokens = (
            s.llm_term_extraction_batch_max_tokens
            if s.llm_term_extraction_batch_max_tokens is not None
            else 600
        )
        self.llm_term_extraction_batch_max_paragraphs = (
            s.llm_term_extraction_batch_max_paragraphs
            if s.llm_term_extraction_batch_max_paragraphs is not None
            else 12
        )

        if self.ocr_workaround:
            self.remove_non_formula_lines = False

        self.tm_mode = s.tm_mode
        self.tm_scope = s.tm_scope
        self.tm_min_segment_chars = s.tm_min_segment_chars
        self.tm_fuzzy_min_score = s.tm_fuzzy_min_score
        self.tm_semantic_min_similarity = s.tm_semantic_min_similarity
        self.tm_project_id = s.tm_project_id or ""
        self.tm_embedding_model = s.tm_embedding_model
        self.tm_import_path = s.tm_import_path
        self.tm_export_path = s.tm_export_path

        self.ocr_mode = (s.ocr_mode or "off").strip().lower()
        if self.ocr_mode not in ("off", "auto", "force", "hybrid"):
            raise ValueError(
                f"ocr_mode must be one of off|auto|force|hybrid, got {s.ocr_mode!r}",
            )
        self.ocr_pages = s.ocr_pages
        self.ocr_page_ranges = self.parse_pages(s.ocr_pages) if s.ocr_pages else None
        self.ocr_lang_hints = list(s.ocr_lang_hints) if s.ocr_lang_hints else []
        self.ocr_debug_dump = bool(
            s.ocr_debug_dump or (s.debug and self.ocr_mode != "off"),
        )
        self.ocr_scanned_ssim_threshold = float(s.ocr_scanned_ssim_threshold)
        self.ocr_low_text_density_threshold = float(s.ocr_low_text_density_threshold)
        self.original_page_ranges: list[tuple[int, int]] | None = (
            list(self.page_ranges) if self.page_ranges else None
        )
        self.split_part_origin_offset: int = int(s.split_part_origin_offset)
        self.ocr_glyph_clear_disabled: bool = False
        self.last_ocr_routing_report: dict | None = None

        self._apply_translation_memory_to_translators()

    def _tm_document_scope(self) -> str:
        try:
            p = Path(self.input_file).resolve()
        except OSError:
            p = Path(str(self.input_file))
        digest = hashlib.sha256(str(p).encode("utf-8", errors="replace")).hexdigest()
        return digest[:24]

    def _apply_translation_memory_to_translators(self) -> None:
        pairs = flatten_glossary_entries_from_config(self)
        gsig = glossary_signature_from_pairs(pairs)
        rt = TMRuntimeConfig(
            mode=TMRuntimeConfig.parse_mode(self.tm_mode),
            scope=TMRuntimeConfig.parse_scope(self.tm_scope),
            min_segment_chars=self.tm_min_segment_chars,
            fuzzy_min_score=self.tm_fuzzy_min_score,
            semantic_min_similarity=self.tm_semantic_min_similarity,
            embedding_model=self.tm_embedding_model,
        )
        doc_scope = self._tm_document_scope()
        proj_scope = (self.tm_project_id or "")[:512]
        for tr in (self.translator, self.term_extraction_translator):
            cache = getattr(tr, "cache", None)
            if cache is None:
                continue
            if self.tm_import_path:
                ip = Path(self.tm_import_path)
                if ip.is_file():
                    cache.import_tm_ndjson(ip)
            cache.configure_tm_runtime(
                tm_runtime=rt,
                document_scope=doc_scope,
                project_scope=proj_scope,
                glossary_signature=gsig,
                glossary_pairs=pairs,
            )

    def refresh_translation_memory_glossary_context(self) -> None:
        """Call after auto-extracted glossary is finalized so TM safety matches prompts."""
        self._apply_translation_memory_to_translators()

    def run_tm_export_if_configured(self) -> None:
        """Write TM NDJSON for the main translator fingerprint (after a job)."""
        if not self.tm_export_path:
            return
        outp = Path(self.tm_export_path)
        cache = getattr(self.translator, "cache", None)
        if cache is None:
            return
        if outp.is_dir():
            stem = Path(str(self.input_file)).stem
            outp = outp / f"{stem}.tm.ndjson"
        cache.export_tm_ndjson(outp)

    def parse_pages(self, pages_str: str | None) -> list[tuple[int, int]] | None:
        """解析页码字符串，返回页码范围列表

        Args:
            pages_str: 形如 "1-,2,-3,4" 的页码字符串

        Returns:
            包含 (start, end) 元组的列表，其中 -1 表示无限制
        """
        if not pages_str:
            return None

        ranges: list[tuple[int, int]] = []
        for part in pages_str.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-")
                start_as_int = int(start) if start else 1
                end_as_int = int(end) if end else -1
                ranges.append((start_as_int, end_as_int))
            else:
                page = int(part)
                ranges.append((page, page))
        return ranges

    def should_translate_page(self, page_number: int) -> bool:
        """判断指定页码是否需要翻译
        Args:
            page_number: 页码
        Returns:
            是否需要翻译该页
        """
        if isinstance(self.page_ranges, list) and len(self.page_ranges) == 0:
            return False
        if not self.page_ranges:
            return True

        for start, end in self.page_ranges:
            if start <= page_number and (end == -1 or page_number <= end):
                return True
        return False

    def global_page_1based(self, local_page_number_0based: int) -> int:
        """Map a 0-based page index in the current (possibly split) PDF to 1-based original doc page."""
        return self.split_part_origin_offset + int(local_page_number_0based) + 1

    def should_translate_global_page(self, global_1based: int) -> bool:
        """Like should_translate_page but uses original document page numbers (same as --pages)."""
        ranges = self.original_page_ranges
        if isinstance(ranges, list) and len(ranges) == 0:
            return False
        if not ranges:
            return True
        for start, end in ranges:
            if start <= global_1based and (end == -1 or global_1based <= end):
                return True
        return False

    def ocr_pages_allow_global(self, global_1based: int) -> bool:
        """If --ocr-pages is set, OCR is only allowed on those original pages."""
        if not self.ocr_page_ranges:
            return True
        for start, end in self.ocr_page_ranges:
            if start <= global_1based and (end == -1 or global_1based <= end):
                return True
        return False

    def get_output_file_path(self, filename: str) -> Path:
        return Path(self.output_dir) / filename

    def get_working_file_path(self, filename: str) -> Path:
        return Path(self.working_dir) / filename

    def get_part_working_dir(self, part_index: int) -> Path:
        """Get working directory for a specific part"""
        if part_index not in self._part_working_dirs:
            if self.working_dir:
                part_dir = Path(self.working_dir) / f"part_{part_index}"
            else:
                part_dir = Path(tempfile.mkdtemp()) / f"part_{part_index}"
            part_dir.mkdir(parents=True, exist_ok=True)
            self._part_working_dirs[part_index] = part_dir
        return self._part_working_dirs[part_index]

    def get_part_output_dir(self, part_index: int) -> Path:
        """Get output directory for a specific part"""
        if part_index not in self._part_output_dirs:
            part_dir = Path(self.working_dir) / f"part_{part_index}_output"
            part_dir.mkdir(parents=True, exist_ok=True)
            self._part_output_dirs[part_index] = part_dir
        return self._part_output_dirs[part_index]

    def cleanup_part_output_dir(self, part_index: int):
        """Clean up output directory for a specific part"""
        if part_index in self._part_output_dirs:
            part_dir = self._part_output_dirs[part_index]
            if part_dir.exists():
                shutil.rmtree(part_dir)
            del self._part_output_dirs[part_index]

    def cleanup_part_working_dir(self, part_index: int):
        """Clean up working directory for a specific part"""
        if part_index in self._part_working_dirs:
            part_dir = self._part_working_dirs[part_index]
            if part_dir.exists():
                shutil.rmtree(part_dir, ignore_errors=True)
            del self._part_working_dirs[part_index]

    def cleanup_temp_files(self):
        """Clean up all temporary files including part working directories"""
        try:
            for part_index in list(self._part_working_dirs.keys()):
                self.cleanup_part_working_dir(part_index)
            if self._is_temp_dir:
                logger.info(f"cleanup temp files: {self.working_dir}")
                shutil.rmtree(self.working_dir, ignore_errors=True)
        except Exception:
            logger.exception("Error cleaning up temporary files")

    def raise_if_cancelled(self):
        if self.progress_monitor is not None:
            self.progress_monitor.raise_if_cancelled()

    def cancel_translation(self):
        if self.progress_monitor is not None:
            self.progress_monitor.cancel()

    def get_term_extraction_translator(self) -> BaseTranslator:
        """Return the translator to use for automatic term extraction."""
        return self.term_extraction_translator

    def record_term_extraction_usage(
        self,
        total_tokens: int,
        prompt_tokens: int,
        completion_tokens: int,
        cache_hit_prompt_tokens: int,
    ) -> None:
        """Accumulate token usage for automatic term extraction."""
        if total_tokens > 0:
            self.term_extraction_token_usage["total_tokens"] += total_tokens
        if prompt_tokens > 0:
            self.term_extraction_token_usage["prompt_tokens"] += prompt_tokens
        if completion_tokens > 0:
            self.term_extraction_token_usage["completion_tokens"] += completion_tokens
        if cache_hit_prompt_tokens > 0:
            self.term_extraction_token_usage["cache_hit_prompt_tokens"] += (
                cache_hit_prompt_tokens
            )


class TranslateResult:
    original_pdf_path: str
    total_seconds: float
    mono_plain_pdf: Path | None
    mono_watermarked_pdf: Path | None
    dual_plain_pdf: Path | None
    dual_watermarked_pdf: Path | None
    peak_memory_usage: int | None
    auto_extracted_glossary_path: Path | None
    total_valid_character_count: int | None
    total_valid_text_token_count: int | None

    def __init__(
        self,
        mono_plain_pdf: Path | None,
        dual_plain_pdf: Path | None,
        auto_extracted_glossary_path: Path | None = None,
        *,
        mono_watermarked_pdf: Path | None = None,
        dual_watermarked_pdf: Path | None = None,
    ):
        self.mono_plain_pdf = mono_plain_pdf
        self.dual_plain_pdf = dual_plain_pdf
        self.mono_watermarked_pdf = mono_watermarked_pdf or mono_plain_pdf
        self.dual_watermarked_pdf = dual_watermarked_pdf or dual_plain_pdf

        self.auto_extracted_glossary_path = auto_extracted_glossary_path
        self.total_valid_character_count = None
        self.total_valid_text_token_count = None

    def __str__(self):
        """Return a human-readable string representation of the translation result."""
        result = []
        if hasattr(self, "original_pdf_path") and self.original_pdf_path:
            result.append(f"\tOriginal PDF: {self.original_pdf_path}")

        if hasattr(self, "total_seconds") and self.total_seconds:
            result.append(f"\tTotal time: {self.total_seconds:.2f} seconds")

        if self.mono_watermarked_pdf:
            result.append(f"\tMonolingual PDF: {self.mono_watermarked_pdf}")

        if self.dual_watermarked_pdf:
            result.append(f"\tDual-language PDF: {self.dual_watermarked_pdf}")

        if (
            self.mono_plain_pdf
            and self.mono_watermarked_pdf
            and self.mono_plain_pdf != self.mono_watermarked_pdf
        ):
            result.append(f"\tPlain monolingual PDF: {self.mono_plain_pdf}")

        if (
            self.dual_plain_pdf
            and self.dual_watermarked_pdf
            and self.dual_plain_pdf != self.dual_watermarked_pdf
        ):
            result.append(f"\tPlain dual-language PDF: {self.dual_plain_pdf}")

        if (
            hasattr(self, "auto_extracted_glossary_path")
            and self.auto_extracted_glossary_path
        ):
            result.append(
                f"\tAuto-extracted glossary: {self.auto_extracted_glossary_path}"
            )

        if hasattr(self, "peak_memory_usage") and self.peak_memory_usage:
            result.append(f"\tPeak memory usage: {self.peak_memory_usage} MB")

        if hasattr(self, "total_valid_character_count") and isinstance(
            self.total_valid_character_count, int
        ):
            result.append(
                f"\tTotal valid character count: {self.total_valid_character_count}"
            )

        if hasattr(self, "total_valid_text_token_count") and isinstance(
            self.total_valid_text_token_count, int
        ):
            result.append(
                f"\tTotal valid text token count (gpt-4o): {self.total_valid_text_token_count}"
            )

        if result:
            result.insert(0, "Translation results:")

        return "\n".join(result) if result else "No translation results available"
