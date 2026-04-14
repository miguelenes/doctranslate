import logging

import cv2
import numpy as np
import pymupdf
import regex
from skimage.metrics import structural_similarity

from doctranslate.exceptions import ScannedPDFError
from doctranslate.format.pdf.document_il import il_version_1
from doctranslate.format.pdf.document_il.backend.pdf_creater import PDFCreater
from doctranslate.format.pdf.document_il.utils.style_helper import BLACK
from doctranslate.format.pdf.document_il.utils.style_helper import GREEN
from doctranslate.format.pdf.translation_config import TranslationConfig

logger = logging.getLogger(__name__)


class DetectScannedFile:
    stage_name = "DetectScannedFile"

    def __init__(self, translation_config: TranslationConfig):
        self.translation_config = translation_config

    def _save_debug_box_to_page(self, page: il_version_1.Page, similarity: float):
        """Save debug boxes and text labels to the PDF page."""
        if not self.translation_config.debug:
            return

        color = GREEN

        # Create text label at top-left corner
        # Note: PDF coordinates are from bottom-left,
        # so we use y2 for top position
        style = il_version_1.PdfStyle(
            font_id="base",
            font_size=4,
            graphic_state=color,
        )
        page_width = page.cropbox.box.x2 - page.cropbox.box.x
        page_height = page.cropbox.box.y2 - page.cropbox.box.y
        unicode = f"scanned score: {similarity * 100:.2f} %"
        page.pdf_paragraph.append(
            il_version_1.PdfParagraph(
                first_line_indent=False,
                box=il_version_1.Box(
                    x=page.cropbox.box.x + page_width * 0.03,
                    y=page.cropbox.box.y,
                    x2=page.cropbox.box.x2,
                    y2=page.cropbox.box.y2 - page_height * 0.03,
                ),
                vertical=False,
                pdf_style=style,
                unicode=unicode,
                pdf_paragraph_composition=[
                    il_version_1.PdfParagraphComposition(
                        pdf_same_style_unicode_characters=il_version_1.PdfSameStyleUnicodeCharacters(
                            unicode=unicode,
                            pdf_style=style,
                            debug_info=True,
                        ),
                    ),
                ],
                xobj_id=-1,
            ),
        )

    def fast_check(self, doc: pymupdf.Document) -> bool:
        if doc:
            hit_list = [0] * len(doc)
            for page in doc:
                contents_list = page.get_contents()
                for index in contents_list:
                    contents = doc.xref_stream(index)
                    if regex.search(
                        rb"(/Artifact|/P)(\s*\<\<\s*/MCID\s+|\s+BDC)", contents
                    ):
                        hit_list[page.number] += 1
                    if regex.search(rb"\s3\s+Tr\s", contents):
                        hit_list[page.number] += 1
            return bool(sum(hit_list) > len(doc) * 0.8)
        return False

    def process(
        self, docs: il_version_1.Document, original_pdf_path, mediabox_data: dict
    ):
        """Generate layouts for all pages that need to be translated."""
        # Get pages that need to be translated

        pdf_creater = PDFCreater(
            original_pdf_path, docs, self.translation_config, mediabox_data
        )

        pages_to_translate = [
            page
            for page in docs.page
            if self.translation_config.should_translate_page(page.page_number + 1)
        ]
        if not pages_to_translate:
            return
        mupdf = pymupdf.open(self.translation_config.get_working_file_path("input.pdf"))
        total = len(pages_to_translate)
        threshold = 0.8 * total
        threshold = max(threshold, 1)
        scanned = 0
        non_scanned = 0
        non_scanned_threshold = total - threshold
        ssim_cut = self.translation_config.ocr_scanned_ssim_threshold
        need_all_page_scores = self.translation_config.ocr_mode != "off"
        with self.translation_config.progress_monitor.stage_start(
            self.stage_name,
            total,
        ) as progress:
            for page in pages_to_translate:
                global_idx = (
                    self.translation_config.split_part_origin_offset + page.page_number
                )
                if (
                    not need_all_page_scores
                    and scanned < threshold
                    and non_scanned < non_scanned_threshold
                ):
                    is_scanned, similarity = self.detect_page_is_scanned_with_score(
                        page, mupdf, pdf_creater, ssim_cut
                    )
                    self.translation_config.shared_context_cross_split_part.page_scan_ssim[
                        global_idx
                    ] = similarity
                    self.translation_config.shared_context_cross_split_part.page_scan_is_scanned[
                        global_idx
                    ] = is_scanned
                    if is_scanned:
                        scanned += 1
                    else:
                        non_scanned += 1
                elif need_all_page_scores:
                    is_scanned, similarity = self.detect_page_is_scanned_with_score(
                        page, mupdf, pdf_creater, ssim_cut
                    )
                    self.translation_config.shared_context_cross_split_part.page_scan_ssim[
                        global_idx
                    ] = similarity
                    self.translation_config.shared_context_cross_split_part.page_scan_is_scanned[
                        global_idx
                    ] = is_scanned
                    if is_scanned:
                        scanned += 1
                    else:
                        non_scanned += 1
                else:
                    # We have enough information to determine document type
                    non_scanned += 1
                progress.advance(1)

        if scanned >= threshold:
            if self.translation_config.ocr_mode != "off":
                logger.warning(
                    "Detected %s scanned pages (>=80%% of translatable pages). "
                    "Continuing with OCR routing (ocr_mode=%s).",
                    scanned,
                    self.translation_config.ocr_mode,
                )
                return
            if self.translation_config.auto_enable_ocr_workaround:
                logger.warning(
                    f"Detected {scanned} scanned pages, which is more than 80% of the total pages. "
                    "Turning on OCR workaround.",
                )
                self.translation_config.shared_context_cross_split_part.auto_enabled_ocr_workaround = True
                self.translation_config.ocr_workaround = True
                self.translation_config.skip_scanned_detection = True
                self.translation_config.disable_rich_text_translate = True
                self.clean_render_order_for_chars(docs)
                self.translation_config.remove_non_formula_lines = False
            else:
                logger.warning(
                    f"Detected {scanned} scanned pages, which is more than 80% of the total pages. "
                    "Please check the input PDF file.",
                )
                raise ScannedPDFError("Scanned PDF detected.")

    def clean_render_order_for_chars(self, docs: il_version_1.Document):
        for page in docs.page:
            for char in page.pdf_character:
                char.render_order = None
                if not char.debug_info:
                    char.pdf_style.graphic_state = BLACK

    def detect_page_is_scanned_with_score(
        self,
        page: il_version_1.Page,
        pdf: pymupdf.Document,
        pdf_creater: PDFCreater,
        ssim_threshold: float,
    ) -> tuple[bool, float]:
        before_page_image = pdf[page.page_number].get_pixmap()
        before_page_image = np.frombuffer(before_page_image.samples, np.uint8).reshape(
            before_page_image.height,
            before_page_image.width,
            3,
        )[:, :, ::-1]

        pdf_creater.update_page_content_stream(
            False, page, pdf, self.translation_config, True
        )

        after_page_image = pdf[page.page_number].get_pixmap()
        after_page_image = np.frombuffer(after_page_image.samples, np.uint8).reshape(
            after_page_image.height,
            after_page_image.width,
            3,
        )[:, :, ::-1]
        before_page_image = cv2.cvtColor(before_page_image, cv2.COLOR_RGB2GRAY)
        after_page_image = cv2.cvtColor(after_page_image, cv2.COLOR_RGB2GRAY)
        similarity = float(
            structural_similarity(before_page_image, after_page_image),
        )
        is_scanned = similarity > ssim_threshold
        self._save_debug_box_to_page(page, similarity)
        return is_scanned, similarity

    def detect_page_is_scanned(
        self, page: il_version_1.Page, pdf: pymupdf.Document, pdf_creater: PDFCreater
    ) -> bool:
        ssim_cut = self.translation_config.ocr_scanned_ssim_threshold
        scanned, _ = self.detect_page_is_scanned_with_score(
            page, pdf, pdf_creater, ssim_cut
        )
        return scanned
