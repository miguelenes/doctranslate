from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.job_event_item import JobEventItem


T = TypeVar("T", bound="JobEventsResponse")


@_attrs_define
class JobEventsResponse:
    """
    Attributes:
        job_id (str):
        items (list[JobEventItem] | Unset):
        schema_version (str | Unset):  Default: '1'.
    """

    job_id: str
    items: list[JobEventItem] | Unset = UNSET
    schema_version: str | Unset = "1"

    def to_dict(self) -> dict[str, Any]:
        job_id = self.job_id

        items: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.items, Unset):
            items = []
            for items_item_data in self.items:
                items_item = items_item_data.to_dict()
                items.append(items_item)

        schema_version = self.schema_version

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "job_id": job_id,
            }
        )
        if items is not UNSET:
            field_dict["items"] = items
        if schema_version is not UNSET:
            field_dict["schema_version"] = schema_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.job_event_item import JobEventItem

        d = dict(src_dict)
        job_id = d.pop("job_id")

        _items = d.pop("items", UNSET)
        items: list[JobEventItem] | Unset = UNSET
        if _items is not UNSET:
            items = []
            for items_item_data in _items:
                items_item = JobEventItem.from_dict(items_item_data)

                items.append(items_item)

        schema_version = d.pop("schema_version", UNSET)

        job_events_response = cls(
            job_id=job_id,
            items=items,
            schema_version=schema_version,
        )

        return job_events_response
