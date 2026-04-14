from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.translation_error_payload import TranslationErrorPayload


T = TypeVar("T", bound="TranslationErrorEvent")


@_attrs_define
class TranslationErrorEvent:
    """
    Attributes:
        error (TranslationErrorPayload): Structured error for API/CLI consumers.
        event_version (str | Unset):  Default: '1'.
        schema_version (str | Unset):  Default: '1'.
        type_ (Literal['error'] | Unset):  Default: 'error'.
    """

    error: TranslationErrorPayload
    event_version: str | Unset = "1"
    schema_version: str | Unset = "1"
    type_: Literal["error"] | Unset = "error"

    def to_dict(self) -> dict[str, Any]:
        error = self.error.to_dict()

        event_version = self.event_version

        schema_version = self.schema_version

        type_ = self.type_

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "error": error,
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
        from ..models.translation_error_payload import TranslationErrorPayload

        d = dict(src_dict)
        error = TranslationErrorPayload.from_dict(d.pop("error"))

        event_version = d.pop("event_version", UNSET)

        schema_version = d.pop("schema_version", UNSET)

        type_ = cast(Literal["error"] | Unset, d.pop("type", UNSET))
        if type_ != "error" and not isinstance(type_, Unset):
            raise ValueError(f"type must match const 'error', got '{type_}'")

        translation_error_event = cls(
            error=error,
            event_version=event_version,
            schema_version=schema_version,
            type_=type_,
        )

        return translation_error_event
