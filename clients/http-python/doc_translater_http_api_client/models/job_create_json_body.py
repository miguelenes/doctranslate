from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.translation_request import TranslationRequest
    from ..models.webhook_create_spec import WebhookCreateSpec


T = TypeVar("T", bound="JobCreateJsonBody")


@_attrs_define
class JobCreateJsonBody:
    """Typed JSON job creation (alternative to multipart ``POST /v1/jobs``).

    Attributes:
        translation_request (TranslationRequest): Stable, versioned request to run one PDF translation job.
        input_pdf_base64 (None | str | Unset): Optional standard-base64 PDF bytes. When set, the server writes a temp
            file and overrides ``translation_request.input_pdf``.
        webhook (None | Unset | WebhookCreateSpec):
    """

    translation_request: TranslationRequest
    input_pdf_base64: None | str | Unset = UNSET
    webhook: None | Unset | WebhookCreateSpec = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.webhook_create_spec import WebhookCreateSpec

        translation_request = self.translation_request.to_dict()

        input_pdf_base64: None | str | Unset
        if isinstance(self.input_pdf_base64, Unset):
            input_pdf_base64 = UNSET
        else:
            input_pdf_base64 = self.input_pdf_base64

        webhook: dict[str, Any] | None | Unset
        if isinstance(self.webhook, Unset):
            webhook = UNSET
        elif isinstance(self.webhook, WebhookCreateSpec):
            webhook = self.webhook.to_dict()
        else:
            webhook = self.webhook

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "translation_request": translation_request,
            }
        )
        if input_pdf_base64 is not UNSET:
            field_dict["input_pdf_base64"] = input_pdf_base64
        if webhook is not UNSET:
            field_dict["webhook"] = webhook

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.translation_request import TranslationRequest
        from ..models.webhook_create_spec import WebhookCreateSpec

        d = dict(src_dict)
        translation_request = TranslationRequest.from_dict(d.pop("translation_request"))

        def _parse_input_pdf_base64(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        input_pdf_base64 = _parse_input_pdf_base64(d.pop("input_pdf_base64", UNSET))

        def _parse_webhook(data: object) -> None | Unset | WebhookCreateSpec:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                webhook_type_0 = WebhookCreateSpec.from_dict(data)

                return webhook_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | WebhookCreateSpec, data)

        webhook = _parse_webhook(d.pop("webhook", UNSET))

        job_create_json_body = cls(
            translation_request=translation_request,
            input_pdf_base64=input_pdf_base64,
            webhook=webhook,
        )

        return job_create_json_body
