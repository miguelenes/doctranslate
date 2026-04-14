from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..models.public_error_code import PublicErrorCode, check_public_error_code
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.translation_error_payload_details import TranslationErrorPayloadDetails


T = TypeVar("T", bound="TranslationErrorPayload")


@_attrs_define
class TranslationErrorPayload:
    """Structured error for API/CLI consumers.

    Attributes:
        code (PublicErrorCode): Machine-readable error codes for public API and JSON CLI.
        message (str):
        details (TranslationErrorPayloadDetails | Unset):
        retryable (bool | Unset):  Default: False.
    """

    code: PublicErrorCode
    message: str
    details: TranslationErrorPayloadDetails | Unset = UNSET
    retryable: bool | Unset = False

    def to_dict(self) -> dict[str, Any]:
        code: str = self.code

        message = self.message

        details: dict[str, Any] | Unset = UNSET
        if not isinstance(self.details, Unset):
            details = self.details.to_dict()

        retryable = self.retryable

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "code": code,
                "message": message,
            }
        )
        if details is not UNSET:
            field_dict["details"] = details
        if retryable is not UNSET:
            field_dict["retryable"] = retryable

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.translation_error_payload_details import TranslationErrorPayloadDetails

        d = dict(src_dict)
        code = check_public_error_code(d.pop("code"))

        message = d.pop("message")

        _details = d.pop("details", UNSET)
        details: TranslationErrorPayloadDetails | Unset
        if isinstance(_details, Unset):
            details = UNSET
        else:
            details = TranslationErrorPayloadDetails.from_dict(_details)

        retryable = d.pop("retryable", UNSET)

        translation_error_payload = cls(
            code=code,
            message=message,
            details=details,
            retryable=retryable,
        )

        return translation_error_payload
