from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.translation_error_payload import TranslationErrorPayload


T = TypeVar("T", bound="ApiErrorEnvelope")


@_attrs_define
class ApiErrorEnvelope:
    """Standard JSON error body for HTTP API.

    Attributes:
        error (TranslationErrorPayload): Structured error for API/CLI consumers.
        ok (bool | Unset):  Default: False.
        request_id (None | str | Unset):
        schema_version (str | Unset):  Default: '1'.
    """

    error: TranslationErrorPayload
    ok: bool | Unset = False
    request_id: None | str | Unset = UNSET
    schema_version: str | Unset = "1"

    def to_dict(self) -> dict[str, Any]:
        error = self.error.to_dict()

        ok = self.ok

        request_id: None | str | Unset
        if isinstance(self.request_id, Unset):
            request_id = UNSET
        else:
            request_id = self.request_id

        schema_version = self.schema_version

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "error": error,
            }
        )
        if ok is not UNSET:
            field_dict["ok"] = ok
        if request_id is not UNSET:
            field_dict["request_id"] = request_id
        if schema_version is not UNSET:
            field_dict["schema_version"] = schema_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.translation_error_payload import TranslationErrorPayload

        d = dict(src_dict)
        error = TranslationErrorPayload.from_dict(d.pop("error"))

        ok = d.pop("ok", UNSET)

        def _parse_request_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        request_id = _parse_request_id(d.pop("request_id", UNSET))

        schema_version = d.pop("schema_version", UNSET)

        api_error_envelope = cls(
            error=error,
            ok=ok,
            request_id=request_id,
            schema_version=schema_version,
        )

        return api_error_envelope
