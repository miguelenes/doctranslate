"""HTTP Range header parsing for artifact downloads."""

from __future__ import annotations

import re


def parse_bytes_range(
    range_header: str | None,
    file_size: int,
) -> tuple[int, int] | None | str:
    """
    Parse ``Range: bytes=…`` for a file of ``file_size`` bytes.

    Returns:
        ``None`` if the header is absent or should be ignored (send full file).
        ``(start, end)`` inclusive indices for a single range response.
        ``"unsatisfiable"`` if the range is invalid (HTTP 416).
    """
    if file_size < 0 or range_header is None:
        return None
    raw = range_header.strip()
    if not raw.startswith("bytes="):
        return None
    spec = raw.removeprefix("bytes=").strip()
    if "," in spec:
        return "unsatisfiable"
    m = re.match(r"^(\d*)-(\d*)$", spec)
    if not m:
        return "unsatisfiable"
    start_s, end_s = m.group(1), m.group(2)
    if start_s == "" and end_s == "":
        return "unsatisfiable"
    if start_s == "":
        suffix = int(end_s)
        if suffix <= 0:
            return "unsatisfiable"
        start = max(0, file_size - suffix)
        end = file_size - 1
        if start > end:
            return "unsatisfiable"
        return (start, end)
    start = int(start_s)
    if end_s == "":
        if start >= file_size:
            return "unsatisfiable"
        end = file_size - 1
    else:
        end = int(end_s)
        if start > end or start >= file_size:
            return "unsatisfiable"
        end = min(end, file_size - 1)
    return (start, end)
