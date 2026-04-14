from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="InputFileInspection")


@_attrs_define
class InputFileInspection:
    """Per-file PDF inspection (no translation).

    Attributes:
        page_count (int):
        path (str):
        prior_translated_marker (bool | None | Unset):
    """

    page_count: int
    path: str
    prior_translated_marker: bool | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        page_count = self.page_count

        path = self.path

        prior_translated_marker: bool | None | Unset
        if isinstance(self.prior_translated_marker, Unset):
            prior_translated_marker = UNSET
        else:
            prior_translated_marker = self.prior_translated_marker

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "page_count": page_count,
                "path": path,
            }
        )
        if prior_translated_marker is not UNSET:
            field_dict["prior_translated_marker"] = prior_translated_marker

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        page_count = d.pop("page_count")

        path = d.pop("path")

        def _parse_prior_translated_marker(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        prior_translated_marker = _parse_prior_translated_marker(d.pop("prior_translated_marker", UNSET))

        input_file_inspection = cls(
            page_count=page_count,
            path=path,
            prior_translated_marker=prior_translated_marker,
        )

        return input_file_inspection
