from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="StageWeight")


@_attrs_define
class StageWeight:
    """
    Attributes:
        name (str):
        percent (float):
    """

    name: str
    percent: float

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        percent = self.percent

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "percent": percent,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        percent = d.pop("percent")

        stage_weight = cls(
            name=name,
            percent=percent,
        )

        return stage_weight
