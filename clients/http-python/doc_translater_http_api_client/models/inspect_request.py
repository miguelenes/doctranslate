from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

T = TypeVar("T", bound="InspectRequest")


@_attrs_define
class InspectRequest:
    """
    Attributes:
        paths (list[str]):
    """

    paths: list[str]

    def to_dict(self) -> dict[str, Any]:
        paths = self.paths

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "paths": paths,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        paths = cast(list[str], d.pop("paths"))

        inspect_request = cls(
            paths=paths,
        )

        return inspect_request
