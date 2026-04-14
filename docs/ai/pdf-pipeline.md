# PDF pipeline and stages

The public PDF path is driven from `doctranslate.format.pdf.high_level`. Stages are listed in `TRANSLATE_STAGES` (order and rough cost weights).

## Stage order (canonical)

From `TRANSLATE_STAGES` in `doctranslate/format/pdf/high_level.py`:

1. **ILCreater** — Parse PDF and build intermediate representation (IR/IL).
2. **DetectScannedFile** — Scanned-page detection.
3. **LayoutParser** — Page layout (YOLO-based layout model is injected/configured externally).
4. **TableParser** — Tables.
5. **ParagraphFinder** — Paragraph grouping.
6. **StylesAndFormulas** — Styles and formula-like text.
7. **AutomaticTermExtractor** — Glossary term extraction (LLM, often JSON-shaped).
8. **ILTranslator** — Paragraph translation (LLM batches).
9. **Typesetting** — Reflow into geometry.
10. **FontMapper** — Fonts.
11. **PDFCreater** — Drawing instructions.
12. **SUBSET_FONT_STAGE_NAME** — Font subsetting.
13. **SAVE_PDF_STAGE_NAME** — Write PDF.

## Agent guidelines

- Prefer **minimal, stage-local** changes; understand callers in `high_level.py` before reordering stages.
- Translation is **synchronous** on translator instances from the PDF pipeline’s perspective; async appears around progress/threading — see [Async Translation API](../ImplementationDetails/AsyncTranslate/AsyncTranslate.md).
- Metadata and post-save fixes (`add_metadata`, `fix_cmap`, etc.) are part of the output contract; do not strip without tests.

## Related files

- IL creation: `document_il/frontend/il_creater.py`
- Translation midend: `document_il/midend/il_translator.py`, `il_translator_llm_only.py`
- Backend writer: `document_il/backend/pdf_creater.py`
