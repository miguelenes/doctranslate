from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ConfigValidateResponse")


@_attrs_define
class ConfigValidateResponse:
    """
    Attributes:
        ok (bool | Unset):  Default: True.
        schema_version (str | Unset):  Default: '1'.
        translation_request_valid (bool | None | Unset):
        translator_config_valid (bool | None | Unset):
    """

    ok: bool | Unset = True
    schema_version: str | Unset = "1"
    translation_request_valid: bool | None | Unset = UNSET
    translator_config_valid: bool | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        ok = self.ok

        schema_version = self.schema_version

        translation_request_valid: bool | None | Unset
        if isinstance(self.translation_request_valid, Unset):
            translation_request_valid = UNSET
        else:
            translation_request_valid = self.translation_request_valid

        translator_config_valid: bool | None | Unset
        if isinstance(self.translator_config_valid, Unset):
            translator_config_valid = UNSET
        else:
            translator_config_valid = self.translator_config_valid

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if ok is not UNSET:
            field_dict["ok"] = ok
        if schema_version is not UNSET:
            field_dict["schema_version"] = schema_version
        if translation_request_valid is not UNSET:
            field_dict["translation_request_valid"] = translation_request_valid
        if translator_config_valid is not UNSET:
            field_dict["translator_config_valid"] = translator_config_valid

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ok = d.pop("ok", UNSET)

        schema_version = d.pop("schema_version", UNSET)

        def _parse_translation_request_valid(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        translation_request_valid = _parse_translation_request_valid(d.pop("translation_request_valid", UNSET))

        def _parse_translator_config_valid(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        translator_config_valid = _parse_translator_config_valid(d.pop("translator_config_valid", UNSET))

        config_validate_response = cls(
            ok=ok,
            schema_version=schema_version,
            translation_request_valid=translation_request_valid,
            translator_config_valid=translator_config_valid,
        )

        return config_validate_response
