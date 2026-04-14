"""Page-level OCR routing and injection before layout/paragraph stages."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pymupdf import Document

from doctranslate.format.pdf.document_il import il_version_1
from doctranslate.format.pdf.document_il.midend.ocr_merge import merge_hybrid_native_ocr
from doctranslate.format.pdf.document_il.midend.ocr_merge import (
    replace_page_characters_with_ocr,
)
from doctranslate.format.pdf.document_il.midend.ocr_merge import (
    text_density_chars_per_sqpt,
)
from doctranslate.format.pdf.document_il.midend.ocr_rapidocr_adapter import (
    ocr_page_to_pdf_characters,
)
from doctranslate.format.pdf.translation_config import TranslationConfig

logger = logging.getLogger(__name__)


class OcrRouting:
    stage_name = "OCRRouting"

    def __init__(self, translation_config: TranslationConfig):
        self.translation_config = translation_config

    def _route_for_page(
        self,
        page: il_version_1.Page,
    ) -> tuple[str, dict[str, Any]]:
        """Return route label and signal dict for one page."""
        sc = self.translation_config.shared_context_cross_split_part
        global_idx = self.translation_config.split_part_origin_offset + page.page_number
        global_1based = self.translation_config.global_page_1based(page.page_number)
        density = text_density_chars_per_sqpt(page)
        ssim = sc.page_scan_ssim.get(global_idx)
        is_scanned = sc.page_scan_is_scanned.get(global_idx)

        signals: dict[str, Any] = {
            "global_page_1based": global_1based,
            "local_page_0based": page.page_number,
            "text_density_chars_per_sqpt": density,
            "scan_ssim": ssim,
            "scan_is_scanned": is_scanned,
        }

        if not self.translation_config.should_translate_page(page.page_number + 1):
            return "native", signals
        if not self.translation_config.should_translate_global_page(global_1based):
            return "native", signals
        if not self.translation_config.ocr_pages_allow_global(global_1based):
            return "native", signals

        mode = self.translation_config.ocr_mode
        if mode == "off":
            return "native", signals

        if mode == "force":
            return "ocr_first", signals

        low_text = density < self.translation_config.ocr_low_text_density_threshold
        scanned_flag = bool(is_scanned) if is_scanned is not None else low_text

        if mode in ("auto", "hybrid"):
            if scanned_flag or low_text:
                return "hybrid" if mode == "hybrid" else "ocr_first", signals
            return "native", signals

        return "native", signals

    def process(
        self, docs: il_version_1.Document, mupdf_doc: Document
    ) -> il_version_1.Document:
        if self.translation_config.ocr_mode == "off":
            self.translation_config.last_ocr_routing_report = {
                "skipped": True,
                "pages": [],
            }
            return docs

        report_pages: list[dict[str, Any]] = []
        total = len(docs.page)
        with self.translation_config.progress_monitor.stage_start(
            self.stage_name,
            max(total, 1),
        ) as progress:
            for page in docs.page:
                self.translation_config.raise_if_cancelled()
                route, signals = self._route_for_page(page)
                entry: dict[str, Any] = {
                    "route": route,
                    **signals,
                    "ocr_char_count": 0,
                }
                if route == "native":
                    report_pages.append(entry)
                    progress.advance(1)
                    continue

                mupdf_page = mupdf_doc[page.page_number]
                try:
                    ocr_chars = ocr_page_to_pdf_characters(
                        mupdf_page,
                        self.translation_config,
                    )
                except Exception:
                    logger.exception(
                        "OCR failed for page %s (global %s); keeping native text",
                        page.page_number,
                        signals.get("global_page_1based"),
                    )
                    entry["route"] = "native"
                    entry["error"] = "ocr_exception"
                    report_pages.append(entry)
                    progress.advance(1)
                    continue

                entry["ocr_char_count"] = len(ocr_chars)
                if not ocr_chars:
                    entry["route"] = "native"
                    entry["error"] = "ocr_empty"
                    report_pages.append(entry)
                    progress.advance(1)
                    continue

                if route == "ocr_first":
                    replace_page_characters_with_ocr(page, ocr_chars)
                else:
                    merge_hybrid_native_ocr(page, ocr_chars)

                self.translation_config.ocr_glyph_clear_disabled = True
                report_pages.append(entry)
                progress.advance(1)

        self.translation_config.last_ocr_routing_report = {
            "skipped": False,
            "ocr_mode": self.translation_config.ocr_mode,
            "pages": report_pages,
        }

        if self.translation_config.ocr_debug_dump:
            outp = Path(
                self.translation_config.get_working_file_path("ocr_routing.json"),
            )
            outp.write_text(
                json.dumps(self.translation_config.last_ocr_routing_report, indent=2),
                encoding="utf-8",
            )

        return docs
