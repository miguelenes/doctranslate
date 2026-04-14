from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProgressUpdateEvent")


@_attrs_define
class ProgressUpdateEvent:
    """
    Attributes:
        overall_progress (float):
        stage (str):
        stage_current (int):
        stage_progress (float):
        stage_total (int):
        event_version (str | Unset):  Default: '1'.
        part_index (int | None | Unset):
        schema_version (str | Unset):  Default: '1'.
        total_parts (int | None | Unset):
        type_ (Literal['progress_update'] | Unset):  Default: 'progress_update'.
    """

    overall_progress: float
    stage: str
    stage_current: int
    stage_progress: float
    stage_total: int
    event_version: str | Unset = "1"
    part_index: int | None | Unset = UNSET
    schema_version: str | Unset = "1"
    total_parts: int | None | Unset = UNSET
    type_: Literal["progress_update"] | Unset = "progress_update"

    def to_dict(self) -> dict[str, Any]:
        overall_progress = self.overall_progress

        stage = self.stage

        stage_current = self.stage_current

        stage_progress = self.stage_progress

        stage_total = self.stage_total

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
                "overall_progress": overall_progress,
                "stage": stage,
                "stage_current": stage_current,
                "stage_progress": stage_progress,
                "stage_total": stage_total,
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
        d = dict(src_dict)
        overall_progress = d.pop("overall_progress")

        stage = d.pop("stage")

        stage_current = d.pop("stage_current")

        stage_progress = d.pop("stage_progress")

        stage_total = d.pop("stage_total")

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

        type_ = cast(Literal["progress_update"] | Unset, d.pop("type", UNSET))
        if type_ != "progress_update" and not isinstance(type_, Unset):
            raise ValueError(f"type must match const 'progress_update', got '{type_}'")

        progress_update_event = cls(
            overall_progress=overall_progress,
            stage=stage,
            stage_current=stage_current,
            stage_progress=stage_progress,
            stage_total=stage_total,
            event_version=event_version,
            part_index=part_index,
            schema_version=schema_version,
            total_parts=total_parts,
            type_=type_,
        )

        return progress_update_event
