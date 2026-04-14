"""HTTP Range parsing for artifact downloads."""

from __future__ import annotations

from doctranslate.http_api.range_requests import parse_bytes_range


def test_parse_bytes_range_absent() -> None:
    assert parse_bytes_range(None, 100) is None
    assert parse_bytes_range("", 100) is None


def test_parse_bytes_range_full_file() -> None:
    assert parse_bytes_range("bytes=0-99", 100) == (0, 99)
    assert parse_bytes_range("bytes=0-", 100) == (0, 99)


def test_parse_bytes_range_suffix() -> None:
    assert parse_bytes_range("bytes=-500", 1000) == (500, 999)


def test_parse_bytes_range_unsatisfiable() -> None:
    assert parse_bytes_range("bytes=1000-2000", 500) == "unsatisfiable"
    assert parse_bytes_range("bytes=", 100) == "unsatisfiable"
