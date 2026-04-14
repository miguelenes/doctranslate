from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.translation_options import TranslationOptions
    from ..models.translator_request_config import TranslatorRequestConfig


T = TypeVar("T", bound="TranslationRequest")


@_attrs_define
class TranslationRequest:
    """Stable, versioned request to run one PDF translation job.

    Attributes:
        input_pdf (str): Path to the input PDF.
        lang_in (str | Unset):  Default: 'en'.
        lang_out (str | Unset):  Default: 'zh'.
        options (None | TranslationOptions | Unset):
        schema_version (str | Unset): Client-declared schema version; must match supported version. Default: '1'.
        translator (TranslatorRequestConfig | Unset): How to build translators for a job.
    """

    input_pdf: str
    lang_in: str | Unset = "en"
    lang_out: str | Unset = "zh"
    options: None | TranslationOptions | Unset = UNSET
    schema_version: str | Unset = "1"
    translator: TranslatorRequestConfig | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.translation_options import TranslationOptions

        input_pdf = self.input_pdf

        lang_in = self.lang_in

        lang_out = self.lang_out

        options: dict[str, Any] | None | Unset
        if isinstance(self.options, Unset):
            options = UNSET
        elif isinstance(self.options, TranslationOptions):
            options = self.options.to_dict()
        else:
            options = self.options

        schema_version = self.schema_version

        translator: dict[str, Any] | Unset = UNSET
        if not isinstance(self.translator, Unset):
            translator = self.translator.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "input_pdf": input_pdf,
            }
        )
        if lang_in is not UNSET:
            field_dict["lang_in"] = lang_in
        if lang_out is not UNSET:
            field_dict["lang_out"] = lang_out
        if options is not UNSET:
            field_dict["options"] = options
        if schema_version is not UNSET:
            field_dict["schema_version"] = schema_version
        if translator is not UNSET:
            field_dict["translator"] = translator

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.translation_options import TranslationOptions
        from ..models.translator_request_config import TranslatorRequestConfig

        d = dict(src_dict)
        input_pdf = d.pop("input_pdf")

        lang_in = d.pop("lang_in", UNSET)

        lang_out = d.pop("lang_out", UNSET)

        def _parse_options(data: object) -> None | TranslationOptions | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                options_type_0 = TranslationOptions.from_dict(data)

                return options_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TranslationOptions | Unset, data)

        options = _parse_options(d.pop("options", UNSET))

        schema_version = d.pop("schema_version", UNSET)

        _translator = d.pop("translator", UNSET)
        translator: TranslatorRequestConfig | Unset
        if isinstance(_translator, Unset):
            translator = UNSET
        else:
            translator = TranslatorRequestConfig.from_dict(_translator)

        translation_request = cls(
            input_pdf=input_pdf,
            lang_in=lang_in,
            lang_out=lang_out,
            options=options,
            schema_version=schema_version,
            translator=translator,
        )

        return translation_request
