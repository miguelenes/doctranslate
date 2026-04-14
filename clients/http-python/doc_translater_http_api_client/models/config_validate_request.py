from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.translation_request import TranslationRequest
    from ..models.translator_config_validate_spec import TranslatorConfigValidateSpec


T = TypeVar("T", bound="ConfigValidateRequest")


@_attrs_define
class ConfigValidateRequest:
    """
    Attributes:
        translation_request (None | TranslationRequest | Unset):
        translator_config (None | TranslatorConfigValidateSpec | Unset):
    """

    translation_request: None | TranslationRequest | Unset = UNSET
    translator_config: None | TranslatorConfigValidateSpec | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.translation_request import TranslationRequest
        from ..models.translator_config_validate_spec import TranslatorConfigValidateSpec

        translation_request: dict[str, Any] | None | Unset
        if isinstance(self.translation_request, Unset):
            translation_request = UNSET
        elif isinstance(self.translation_request, TranslationRequest):
            translation_request = self.translation_request.to_dict()
        else:
            translation_request = self.translation_request

        translator_config: dict[str, Any] | None | Unset
        if isinstance(self.translator_config, Unset):
            translator_config = UNSET
        elif isinstance(self.translator_config, TranslatorConfigValidateSpec):
            translator_config = self.translator_config.to_dict()
        else:
            translator_config = self.translator_config

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if translation_request is not UNSET:
            field_dict["translation_request"] = translation_request
        if translator_config is not UNSET:
            field_dict["translator_config"] = translator_config

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.translation_request import TranslationRequest
        from ..models.translator_config_validate_spec import TranslatorConfigValidateSpec

        d = dict(src_dict)

        def _parse_translation_request(data: object) -> None | TranslationRequest | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                translation_request_type_0 = TranslationRequest.from_dict(data)

                return translation_request_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TranslationRequest | Unset, data)

        translation_request = _parse_translation_request(d.pop("translation_request", UNSET))

        def _parse_translator_config(data: object) -> None | TranslatorConfigValidateSpec | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                translator_config_type_0 = TranslatorConfigValidateSpec.from_dict(data)

                return translator_config_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TranslatorConfigValidateSpec | Unset, data)

        translator_config = _parse_translator_config(d.pop("translator_config", UNSET))

        config_validate_request = cls(
            translation_request=translation_request,
            translator_config=translator_config,
        )

        return config_validate_request
