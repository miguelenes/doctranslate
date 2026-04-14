import logging
from pathlib import Path

from pymupdf import Document

from doctranslate.format.pdf.document_il.backend.pdf_creater import PDFCreater
from doctranslate.format.pdf.translation_config import TranslateResult
from doctranslate.format.pdf.translation_config import TranslationConfig

logger = logging.getLogger(__name__)


class ResultMerger:
    """Handles merging of split translation results"""

    def __init__(self, translation_config: TranslationConfig):
        self.config = translation_config

    def merge_results(
        self, results: dict[int, TranslateResult | None]
    ) -> TranslateResult:
        """Merge multiple translation results into one"""
        if not results:
            raise ValueError("No results to merge")

        basename = Path(self.config.input_file).stem
        debug_suffix = ".debug" if self.config.debug else ""

        mono_file_name = f"{basename}{debug_suffix}.{self.config.lang_out}.mono.pdf"
        dual_file_name = f"{basename}{debug_suffix}.{self.config.lang_out}.dual.pdf"

        nw_suffix = debug_suffix + ".no_watermark"

        mono_file_name_no_watermark = (
            f"{basename}{nw_suffix}.{self.config.lang_out}.mono.pdf"
        )
        dual_file_name_no_watermark = (
            f"{basename}{nw_suffix}.{self.config.lang_out}.dual.pdf"
        )
        results = {k: v for k, v in results.items() if v is not None}
        sorted_results = dict(sorted(results.items()))

        merged_mono_wm_path = None
        merged_dual_wm_path = None
        merged_mono_plain_path = None
        merged_dual_plain_path = None
        try:
            if (
                any(r.mono_watermarked_pdf for r in results.values())
                and not self.config.no_mono
            ):
                merged_mono_wm_path = self._merge_pdfs(
                    [
                        r.mono_watermarked_pdf
                        for r in sorted_results.values()
                        if r.mono_watermarked_pdf
                    ],
                    mono_file_name,
                    tag="merged_mono",
                )
        except Exception as e:
            logger.error(f"Error merging monolingual PDFs: {e}")
            merged_mono_wm_path = None

        try:
            if (
                any(r.dual_watermarked_pdf for r in results.values())
                and not self.config.no_dual
            ):
                merged_dual_wm_path = self._merge_pdfs(
                    [
                        r.dual_watermarked_pdf
                        for r in sorted_results.values()
                        if r.dual_watermarked_pdf
                    ],
                    dual_file_name,
                    tag="merged_dual",
                )
        except Exception as e:
            logger.error(f"Error merging dual-language PDFs: {e}")
            merged_dual_wm_path = None

        if any(
            r.dual_watermarked_pdf != r.dual_plain_pdf
            or r.mono_watermarked_pdf != r.mono_plain_pdf
            for r in results.values()
        ):
            try:
                if (
                    any(r.mono_plain_pdf for r in results.values())
                    and not self.config.no_mono
                ):
                    merged_mono_plain_path = self._merge_pdfs(
                        [
                            r.mono_plain_pdf
                            for r in sorted_results.values()
                            if r.mono_plain_pdf
                        ],
                        mono_file_name_no_watermark,
                        tag="merged_no_watermark_mono",
                    )
            except Exception as e:
                logger.error(f"Error merging no-watermark PDFs: {e}")
                merged_mono_plain_path = None

            try:
                if (
                    any(r.dual_plain_pdf for r in results.values())
                    and not self.config.no_dual
                ):
                    merged_dual_plain_path = self._merge_pdfs(
                        [
                            r.dual_plain_pdf
                            for r in sorted_results.values()
                            if r.dual_plain_pdf
                        ],
                        "merged_no_watermark_dual.pdf",
                        tag="merged_no_watermark_dual",
                    )
            except Exception as e:
                logger.error(f"Error merging no-watermark PDFs: {e}")
                merged_dual_plain_path = None

        auto_extracted_glossary_path = None
        if (
            self.config.save_auto_extracted_glossary
            and self.config.shared_context_cross_split_part.auto_extracted_glossary
        ):
            auto_extracted_glossary_path = self.config.get_output_file_path(
                f"{basename}{nw_suffix}.{self.config.lang_out}.glossary.csv"
            )
            with auto_extracted_glossary_path.open("w", encoding="utf-8-sig") as f:
                logger.info(
                    f"save auto extracted glossary to {auto_extracted_glossary_path}"
                )
                f.write(
                    self.config.shared_context_cross_split_part.auto_extracted_glossary.to_csv()
                )

        mp = merged_mono_plain_path
        mw = merged_mono_wm_path
        dp = merged_dual_plain_path
        dw = merged_dual_wm_path

        if mp is None:
            mp = mw
        elif mw is None:
            mw = mp

        if dp is None:
            dp = dw
        elif dw is None:
            dw = dp

        merged_result = TranslateResult(
            mono_plain_pdf=mp,
            dual_plain_pdf=dp,
            auto_extracted_glossary_path=auto_extracted_glossary_path,
            mono_watermarked_pdf=mw,
            dual_watermarked_pdf=dw,
        )

        total_time = sum(
            r.total_seconds for r in results.values() if hasattr(r, "total_seconds")
        )
        merged_result.total_seconds = total_time

        return merged_result

    def _merge_pdfs(
        self, pdf_paths: list[str | Path], output_name: str, tag: str
    ) -> Path:
        """Merge multiple PDFs into one"""
        if not pdf_paths:
            return None

        output_path = self.config.get_output_file_path(output_name)
        merged_doc = Document()

        for pdf_path in pdf_paths:
            doc = Document(str(pdf_path))
            merged_doc.insert_pdf(doc)

        merged_doc = PDFCreater.subset_fonts_in_subprocess(
            merged_doc, self.config, tag=tag
        )
        PDFCreater.save_pdf_with_timeout(
            merged_doc, str(output_path), translation_config=self.config
        )

        return output_path
