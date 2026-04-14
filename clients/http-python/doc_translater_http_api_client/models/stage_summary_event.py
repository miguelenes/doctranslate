from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.stage_weight import StageWeight


T = TypeVar("T", bound="StageSummaryEvent")


@_attrs_define
class StageSummaryEvent:
    """
    Attributes:
        stages (list[StageWeight]):
        event_version (str | Unset):  Default: '1'.
        part_index (int | None | Unset):
        schema_version (str | Unset):  Default: '1'.
        total_parts (int | None | Unset):
        type_ (Literal['stage_summary'] | Unset):  Default: 'stage_summary'.
    """

    stages: list[StageWeight]
    event_version: str | Unset = "1"
    part_index: int | None | Unset = UNSET
    schema_version: str | Unset = "1"
    total_parts: int | None | Unset = UNSET
    type_: Literal["stage_summary"] | Unset = "stage_summary"

    def to_dict(self) -> dict[str, Any]:
        stages = []
        for stages_item_data in self.stages:
            stages_item = stages_item_data.to_dict()
            stages.append(stages_item)

        event_version = self.event_version

        part_index: int | None | Unset
        if isinstance(self.part_index, Unset):
            part_index = UNSET
        else:
            part_index = self.part_index

        schema_version = self.schema_version

        total_parts: int | None | Unset
        if isinstance(self.total_parts, Unset):
            total_parts = UNSET
        else:
            total_parts = self.total_parts

        type_ = self.type_

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "stages": stages,
            }
        )
        if event_version is not UNSET:
            field_dict["event_version"] = event_version
        if part_index is not UNSET:
            field_dict["part_index"] = part_index
        if schema_version is not UNSET:
            field_dict["schema_version"] = schema_version
        if total_parts is not UNSET:
            field_dict["total_parts"] = total_parts
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.stage_weight import StageWeight

        d = dict(src_dict)
        stages = []
        _stages = d.pop("stages")
        for stages_item_data in _stages:
            stages_item = StageWeight.from_dict(stages_item_data)

            stages.append(stages_item)

        event_version = d.pop("event_version", UNSET)

        def _parse_part_index(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        part_index = _parse_part_index(d.pop("part_index", UNSET))

        schema_version = d.pop("schema_version", UNSET)

        def _parse_total_parts(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        total_parts = _parse_total_parts(d.pop("total_parts", UNSET))

        type_ = cast(Literal["stage_summary"] | Unset, d.pop("type", UNSET))
        if type_ != "stage_summary" and not isinstance(type_, Unset):
            raise ValueError(f"type must match const 'stage_summary', got '{type_}'")

        stage_summary_event = cls(
            stages=stages,
            event_version=event_version,
            part_index=part_index,
            schema_version=schema_version,
            total_parts=total_parts,
            type_=type_,
        )

        return stage_summary_event
