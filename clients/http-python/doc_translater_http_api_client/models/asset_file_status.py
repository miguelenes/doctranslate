from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="AssetFileStatus")


@_attrs_define
class AssetFileStatus:
    """
    Attributes:
        category (str):
        name (str):
        present (bool):
    """

    category: str
    name: str
    present: bool

    def to_dict(self) -> dict[str, Any]:
        category = self.category

        name = self.name

        present = self.present

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "category": category,
                "name": name,
                "present": present,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        category = d.pop("category")

        name = d.pop("name")

        present = d.pop("present")

        asset_file_status = cls(
            category=category,
            name=name,
            present=present,
        )

        return asset_file_status
