from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.artifact_descriptor import ArtifactDescriptor


T = TypeVar("T", bound="ArtifactManifest")


@_attrs_define
class ArtifactManifest:
    """All artifacts from a completed job.

    Attributes:
        items (list[ArtifactDescriptor] | Unset):
    """

    items: list[ArtifactDescriptor] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        items: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.items, Unset):
            items = []
            for items_item_data in self.items:
                items_item = items_item_data.to_dict()
                items.append(items_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if items is not UNSET:
            field_dict["items"] = items

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.artifact_descriptor import ArtifactDescriptor

        d = dict(src_dict)
        _items = d.pop("items", UNSET)
        items: list[ArtifactDescriptor] | Unset = UNSET
        if _items is not UNSET:
            items = []
            for items_item_data in _items:
                items_item = ArtifactDescriptor.from_dict(items_item_data)

                items.append(items_item)

        artifact_manifest = cls(
            items=items,
        )

        return artifact_manifest
