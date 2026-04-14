# PDF pipeline and stages

The public PDF path is driven from `doctranslate.format.pdf.high_level`. Stages are listed in `TRANSLATE_STAGES` (order and rough cost weights).

## Stage order (canonical)

From `TRANSLATE_STAGES` in `doctranslate/format/pdf/high_level.py`:

1. **ILCreater** — Parse PDF and build intermediate representation (IR/IL).
2. **DetectScannedFile** — Scanned-page detection (SSIM); records per-page scores in shared context when OCR routing is enabled.
3. **OCRRouting** — Optional RapidOCR injection into `pdf_character` before layout (see `--ocr-mode` in [Configuration](../configuration.md)).
4. **LayoutParser** — Page layout (YOLO-based layout model is injected/configured externally).
5. **TableParser** — Tables.
6. **ParagraphFinder** — Paragraph grouping.
7. **StylesAndFormulas** — Styles and formula-like text.
8. **AutomaticTermExtractor** — Glossary term extraction (LLM, often JSON-shaped).
9. **ILTranslator** — Paragraph translation (LLM batches).
10. **Typesetting** — Reflow into geometry.
11. **FontMapper** — Fonts.
12. **PDFCreater** — Drawing instructions.
13. **SUBSET_FONT_STAGE_NAME** — Font subsetting.
14. **SAVE_PDF_STAGE_NAME** — Write PDF.

## Agent guidelines

- Prefer **minimal, stage-local** changes; understand callers in `high_level.py` before reordering stages.
- Translation is **synchronous** on translator instances from the PDF pipeline’s perspective; async appears around progress/threading — see [Async Translation API](../ImplementationDetails/AsyncTranslate/AsyncTranslate.md).
- Metadata and post-save fixes (`add_metadata`, `fix_cmap`, etc.) are part of the output contract; do not strip without tests.

## Related files

- IL creation: `document_il/frontend/il_creater.py`
- Translation midend: `document_il/midend/il_translator.py`, `il_translator_llm_only.py`
- Backend writer: `document_il/backend/pdf_creater.py`
