from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from .. import types
from ..types import UNSET, Unset

T = TypeVar("T", bound="BodyV1JobsCreateMultipart")


@_attrs_define
class BodyV1JobsCreateMultipart:
    """
    Attributes:
        translation_request (str): JSON string of TranslationRequest
        input_pdf (None | str | Unset):
        webhook (None | str | Unset): Optional JSON object: {"url":"https://...","secret":"..."} or secret_env.
    """

    translation_request: str
    input_pdf: None | str | Unset = UNSET
    webhook: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        translation_request = self.translation_request

        input_pdf: None | str | Unset
        if isinstance(self.input_pdf, Unset):
            input_pdf = UNSET
        else:
            input_pdf = self.input_pdf

        webhook: None | str | Unset
        if isinstance(self.webhook, Unset):
            webhook = UNSET
        else:
            webhook = self.webhook

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "translation_request": translation_request,
            }
        )
        if input_pdf is not UNSET:
            field_dict["input_pdf"] = input_pdf
        if webhook is not UNSET:
            field_dict["webhook"] = webhook

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("translation_request", (None, str(self.translation_request).encode(), "text/plain")))

        if not isinstance(self.input_pdf, Unset):
            if isinstance(self.input_pdf, str):
                files.append(("input_pdf", (None, str(self.input_pdf).encode(), "text/plain")))
            else:
                files.append(("input_pdf", (None, str(self.input_pdf).encode(), "text/plain")))

        if not isinstance(self.webhook, Unset):
            if isinstance(self.webhook, str):
                files.append(("webhook", (None, str(self.webhook).encode(), "text/plain")))
            else:
                files.append(("webhook", (None, str(self.webhook).encode(), "text/plain")))

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        translation_request = d.pop("translation_request")

        def _parse_input_pdf(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        input_pdf = _parse_input_pdf(d.pop("input_pdf", UNSET))

        def _parse_webhook(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        webhook = _parse_webhook(d.pop("webhook", UNSET))

        body_v1_jobs_create_multipart = cls(
            translation_request=translation_request,
            input_pdf=input_pdf,
            webhook=webhook,
        )

        body_v1_jobs_create_multipart.additional_properties = d
        return body_v1_jobs_create_multipart

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
