"""Merge native PDF text with OCR-derived characters (hybrid / dedup helpers)."""

from __future__ import annotations

import re

from doctranslate.format.pdf.document_il import il_version_1


def _page_area_sqpt(page: il_version_1.Page) -> float:
    box = page.cropbox.box
    w = float(box.x2 - box.x)
    h = float(box.y2 - box.y)
    return max(w * h, 1e-9)


def text_density_chars_per_sqpt(page: il_version_1.Page) -> float:
    """Heuristic text density for routing when SSIM is unavailable (e.g. split parts)."""
    n = 0
    for ch in page.pdf_character or []:
        u = ch.char_unicode or ""
        if not u.strip():
            continue
        if re.match(r"^\(cid:\d+\)$", u):
            continue
        n += 1
    return n / _page_area_sqpt(page)


def replace_page_characters_with_ocr(
    page: il_version_1.Page,
    ocr_chars: list[il_version_1.PdfCharacter],
) -> None:
    """MVP ocr_first: drop native text characters and use OCR-derived PdfCharacter list."""
    page.pdf_character = list(ocr_chars)


def merge_hybrid_native_ocr(
    page: il_version_1.Page,
    ocr_chars: list[il_version_1.PdfCharacter],
    *,
    iou_replace_threshold: float = 0.35,
) -> None:
    """Advanced hybrid: keep native chars; add OCR chars that do not overlap native text boxes.

    MVP+ behavior: if native density is very low, behave like full replace.
    """
    native = list(page.pdf_character or [])
    if not native:
        page.pdf_character = list(ocr_chars)
        return

    def _union_native_boxes() -> list[tuple[float, float, float, float]]:
        boxes: list[tuple[float, float, float, float]] = []
        for ch in native:
            vb = ch.visual_bbox.box if ch.visual_bbox else ch.box
            if vb is None:
                continue
            boxes.append((vb.x, vb.y, vb.x2, vb.y2))
        return boxes

    def _iou(
        a: tuple[float, float, float, float],
        b: tuple[float, float, float, float],
    ) -> float:
        ax0, ay0, ax1, ay1 = a
        bx0, by0, bx1, by1 = b
        ix0 = max(ax0, bx0)
        iy0 = max(ay0, by0)
        ix1 = min(ax1, bx1)
        iy1 = min(ay1, by1)
        if ix1 <= ix0 or iy1 <= iy0:
            return 0.0
        inter = (ix1 - ix0) * (iy1 - iy0)
        aa = (ax1 - ax0) * (ay1 - ay0)
        bb = (bx1 - bx0) * (by1 - by0)
        union = aa + bb - inter
        return inter / union if union > 0 else 0.0

    native_boxes = _union_native_boxes()
    kept_ocr: list[il_version_1.PdfCharacter] = []
    for och in ocr_chars:
        vb = och.visual_bbox.box if och.visual_bbox else och.box
        if vb is None:
            continue
        ob = (vb.x, vb.y, vb.x2, vb.y2)
        max_iou = 0.0
        for nb in native_boxes:
            max_iou = max(max_iou, _iou(ob, nb))
        if max_iou < iou_replace_threshold:
            kept_ocr.append(och)

    page.pdf_character = native + kept_ocr
