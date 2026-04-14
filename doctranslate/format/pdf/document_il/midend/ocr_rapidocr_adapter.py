"""RapidOCR (onnxruntime) adapter: page image -> IL PdfCharacter objects in PDF space."""

from __future__ import annotations

import logging
import threading
from typing import Any

import numpy as np
from pymupdf import Page

from doctranslate.format.pdf.document_il import il_version_1
from doctranslate.format.pdf.document_il.utils.mupdf_helper import get_no_rotation_img
from doctranslate.format.pdf.document_il.utils.style_helper import BLACK
from doctranslate.format.pdf.translation_config import TranslationConfig

logger = logging.getLogger(__name__)

_rapidocr_lock = threading.Lock()
_rapidocr_engine: Any = None


def _get_engine() -> Any:
    global _rapidocr_engine
    with _rapidocr_lock:
        if _rapidocr_engine is None:
            from rapidocr_onnxruntime import RapidOCR

            _rapidocr_engine = RapidOCR()
        return _rapidocr_engine


def _image_box_to_pdf_rect(
    ix0: float,
    iy0: float,
    ix1: float,
    iy1: float,
    img_h: int,
    img_w: int,
) -> tuple[float, float, float, float]:
    """Map axis-aligned box from OpenCV image space (origin top-left) to IL/PDF user space."""
    ix0 = float(np.clip(ix0, 0, img_w))
    ix1 = float(np.clip(ix1, 0, img_w))
    iy0 = float(np.clip(iy0, 0, img_h))
    iy1 = float(np.clip(iy1, 0, img_h))
    # Match LayoutParser margin convention (±1 pixel) then clip.
    x0 = max(ix0 - 1.0, 0.0)
    x1 = min(ix1 + 1.0, float(img_w))
    y0 = max(float(img_h) - iy1 - 1.0, 0.0)
    y1 = min(float(img_h) - iy0 + 1.0, float(img_h))
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    return x0, y0, x1, y1


def _quad_to_ixy(
    box: list | np.ndarray,
) -> tuple[float, float, float, float]:
    arr = np.asarray(box, dtype=np.float64)
    if arr.size < 8:
        raise ValueError(f"unexpected OCR box shape: {box!r}")
    pts = arr.reshape(-1, 2)
    xs = pts[:, 0]
    ys = pts[:, 1]
    return float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())


def ocr_page_to_pdf_characters(
    mupdf_page: Page,
    translation_config: TranslationConfig,
    *,
    min_score: float = 0.5,
) -> list[il_version_1.PdfCharacter]:
    """Run full RapidOCR on a rendered page and return synthetic PdfCharacter rows."""
    pix = get_no_rotation_img(mupdf_page)
    image = np.frombuffer(pix.samples, np.uint8).reshape(
        pix.height,
        pix.width,
        pix.n,
    )
    if pix.n == 4:
        image = image[:, :, :3]
    # BGR for RapidOCR
    if image.shape[2] == 3:
        image = image[:, :, ::-1]

    img_h, img_w = image.shape[:2]
    engine = _get_engine()
    ocr_res, _elapse = engine(
        image,
        use_det=True,
        use_cls=True,
        use_rec=True,
        text_score=min_score,
    )
    if not ocr_res or not ocr_res[0]:
        logger.debug("RapidOCR returned no lines for page %s", mupdf_page.number)
        return []

    chars_out: list[il_version_1.PdfCharacter] = []
    char_counter = 0
    for row in ocr_res[0]:
        if not row or len(row) < 3:
            continue
        quad, text, score = row[0], row[1], float(row[2])
        if score < min_score:
            continue
        if not text or not str(text).strip():
            continue
        try:
            ix0, iy0, ix1, iy1 = _quad_to_ixy(quad)
        except (ValueError, TypeError):
            continue
        pdf_x0, pdf_y0, pdf_x1, pdf_y1 = _image_box_to_pdf_rect(
            ix0, iy0, ix1, iy1, img_h, img_w
        )
        line_h = max(pdf_y1 - pdf_y0, 1e-3)
        font_size = max(line_h * 0.85, 4.0)
        text_s = str(text)
        n = max(len(text_s), 1)
        cell_w = (pdf_x1 - pdf_x0) / n
        style = il_version_1.PdfStyle(
            font_id="base",
            font_size=font_size,
            graphic_state=BLACK,
        )
        for i, ch in enumerate(text_s):
            cx0 = pdf_x0 + i * cell_w
            cx1 = cx0 + cell_w
            bbox = il_version_1.Box(x=cx0, y=pdf_y0, x2=cx1, y2=pdf_y1)
            vb = il_version_1.VisualBbox(box=il_version_1.Box(cx0, pdf_y0, cx1, pdf_y1))
            chars_out.append(
                il_version_1.PdfCharacter(
                    box=bbox,
                    pdf_character_id=-100000 - char_counter,
                    advance=cell_w,
                    char_unicode=ch,
                    vertical=False,
                    pdf_style=style,
                    xobj_id=0,
                    visual_bbox=vb,
                    render_order=None,
                    sub_render_order=0,
                    debug_info=False,
                ),
            )
            char_counter += 1

    if translation_config.ocr_lang_hints:
        logger.debug(
            "ocr_lang_hints=%s (RapidOCR-onnxruntime language tuning not applied in MVP)",
            translation_config.ocr_lang_hints,
        )

    return chars_out
