from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.translation_result import TranslationResult


T = TypeVar("T", bound="TranslationFinishedEvent")


@_attrs_define
class TranslationFinishedEvent:
    """
    Attributes:
        translation_result (TranslationResult): Stable completion payload (replaces ad hoc TranslateResult for
            embedders).
        event_version (str | Unset):  Default: '1'.
        schema_version (str | Unset):  Default: '1'.
        type_ (Literal['finish'] | Unset):  Default: 'finish'.
    """

    translation_result: TranslationResult
    event_version: str | Unset = "1"
    schema_version: str | Unset = "1"
    type_: Literal["finish"] | Unset = "finish"

    def to_dict(self) -> dict[str, Any]:
        translation_result = self.translation_result.to_dict()

        event_version = self.event_version

        schema_version = self.schema_version

        type_ = self.type_

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "translation_result": translation_result,
            }
        )
        if event_version is not UNSET:
            field_dict["event_version"] = event_version
        if schema_version is not UNSET:
            field_dict["schema_version"] = schema_version
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.translation_result import TranslationResult

        d = dict(src_dict)
        translation_result = TranslationResult.from_dict(d.pop("translation_result"))

        event_version = d.pop("event_version", UNSET)

        schema_version = d.pop("schema_version", UNSET)

        type_ = cast(Literal["finish"] | Unset, d.pop("type", UNSET))
        if type_ != "finish" and not isinstance(type_, Unset):
            raise ValueError(f"type must match const 'finish', got '{type_}'")

        translation_finished_event = cls(
            translation_result=translation_result,
            event_version=event_version,
            schema_version=schema_version,
            type_=type_,
        )

        return translation_finished_event
