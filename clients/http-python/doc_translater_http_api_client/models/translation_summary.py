from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="TranslationSummary")


@_attrs_define
class TranslationSummary:
    """High-level run metrics.

    Attributes:
        original_pdf_path (str):
        peak_memory_usage_mb (float | None | Unset):
        total_seconds (float | None | Unset):
        total_valid_character_count (int | None | Unset):
        total_valid_text_token_count (int | None | Unset):
    """

    original_pdf_path: str
    peak_memory_usage_mb: float | None | Unset = UNSET
    total_seconds: float | None | Unset = UNSET
    total_valid_character_count: int | None | Unset = UNSET
    total_valid_text_token_count: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        original_pdf_path = self.original_pdf_path

        peak_memory_usage_mb: float | None | Unset
        if isinstance(self.peak_memory_usage_mb, Unset):
            peak_memory_usage_mb = UNSET
        else:
            peak_memory_usage_mb = self.peak_memory_usage_mb

        total_seconds: float | None | Unset
        if isinstance(self.total_seconds, Unset):
            total_seconds = UNSET
        else:
            total_seconds = self.total_seconds

        total_valid_character_count: int | None | Unset
        if isinstance(self.total_valid_character_count, Unset):
            total_valid_character_count = UNSET
        else:
            total_valid_character_count = self.total_valid_character_count

        total_valid_text_token_count: int | None | Unset
        if isinstance(self.total_valid_text_token_count, Unset):
            total_valid_text_token_count = UNSET
        else:
            total_valid_text_token_count = self.total_valid_text_token_count

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "original_pdf_path": original_pdf_path,
            }
        )
        if peak_memory_usage_mb is not UNSET:
            field_dict["peak_memory_usage_mb"] = peak_memory_usage_mb
        if total_seconds is not UNSET:
            field_dict["total_seconds"] = total_seconds
        if total_valid_character_count is not UNSET:
            field_dict["total_valid_character_count"] = total_valid_character_count
        if total_valid_text_token_count is not UNSET:
            field_dict["total_valid_text_token_count"] = total_valid_text_token_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        original_pdf_path = d.pop("original_pdf_path")

        def _parse_peak_memory_usage_mb(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        peak_memory_usage_mb = _parse_peak_memory_usage_mb(d.pop("peak_memory_usage_mb", UNSET))

        def _parse_total_seconds(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        total_seconds = _parse_total_seconds(d.pop("total_seconds", UNSET))

        def _parse_total_valid_character_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        total_valid_character_count = _parse_total_valid_character_count(d.pop("total_valid_character_count", UNSET))

        def _parse_total_valid_text_token_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        total_valid_text_token_count = _parse_total_valid_text_token_count(d.pop("total_valid_text_token_count", UNSET))

        translation_summary = cls(
            original_pdf_path=original_pdf_path,
            peak_memory_usage_mb=peak_memory_usage_mb,
            total_seconds=total_seconds,
            total_valid_character_count=total_valid_character_count,
            total_valid_text_token_count=total_valid_text_token_count,
        )

        return translation_summary
