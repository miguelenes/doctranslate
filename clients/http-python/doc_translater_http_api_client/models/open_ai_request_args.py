from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="OpenAIRequestArgs")


@_attrs_define
class OpenAIRequestArgs:
    """Arguments for legacy OpenAI translator construction.

    Attributes:
        api_key (None | str | Unset):
        base_url (None | str | Unset):
        enable_json_mode_if_requested (bool | Unset):  Default: False.
        model (str | Unset):  Default: 'gpt-4o-mini'.
        reasoning (None | str | Unset):
        send_dashscope_header (bool | Unset):  Default: False.
        send_temperature (bool | Unset):  Default: True.
        term_api_key (None | str | Unset):
        term_base_url (None | str | Unset):
        term_model (None | str | Unset):
        term_reasoning (None | str | Unset):
    """

    api_key: None | str | Unset = UNSET
    base_url: None | str | Unset = UNSET
    enable_json_mode_if_requested: bool | Unset = False
    model: str | Unset = "gpt-4o-mini"
    reasoning: None | str | Unset = UNSET
    send_dashscope_header: bool | Unset = False
    send_temperature: bool | Unset = True
    term_api_key: None | str | Unset = UNSET
    term_base_url: None | str | Unset = UNSET
    term_model: None | str | Unset = UNSET
    term_reasoning: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        api_key: None | str | Unset
        if isinstance(self.api_key, Unset):
            api_key = UNSET
        else:
            api_key = self.api_key

        base_url: None | str | Unset
        if isinstance(self.base_url, Unset):
            base_url = UNSET
        else:
            base_url = self.base_url

        enable_json_mode_if_requested = self.enable_json_mode_if_requested

        model = self.model

        reasoning: None | str | Unset
        if isinstance(self.reasoning, Unset):
            reasoning = UNSET
        else:
            reasoning = self.reasoning

        send_dashscope_header = self.send_dashscope_header

        send_temperature = self.send_temperature

        term_api_key: None | str | Unset
        if isinstance(self.term_api_key, Unset):
            term_api_key = UNSET
        else:
            term_api_key = self.term_api_key

        term_base_url: None | str | Unset
        if isinstance(self.term_base_url, Unset):
            term_base_url = UNSET
        else:
            term_base_url = self.term_base_url

        term_model: None | str | Unset
        if isinstance(self.term_model, Unset):
            term_model = UNSET
        else:
            term_model = self.term_model

        term_reasoning: None | str | Unset
        if isinstance(self.term_reasoning, Unset):
            term_reasoning = UNSET
        else:
            term_reasoning = self.term_reasoning

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if api_key is not UNSET:
            field_dict["api_key"] = api_key
        if base_url is not UNSET:
            field_dict["base_url"] = base_url
        if enable_json_mode_if_requested is not UNSET:
            field_dict["enable_json_mode_if_requested"] = enable_json_mode_if_requested
        if model is not UNSET:
            field_dict["model"] = model
        if reasoning is not UNSET:
            field_dict["reasoning"] = reasoning
        if send_dashscope_header is not UNSET:
            field_dict["send_dashscope_header"] = send_dashscope_header
        if send_temperature is not UNSET:
            field_dict["send_temperature"] = send_temperature
        if term_api_key is not UNSET:
            field_dict["term_api_key"] = term_api_key
        if term_base_url is not UNSET:
            field_dict["term_base_url"] = term_base_url
        if term_model is not UNSET:
            field_dict["term_model"] = term_model
        if term_reasoning is not UNSET:
            field_dict["term_reasoning"] = term_reasoning

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_api_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        api_key = _parse_api_key(d.pop("api_key", UNSET))

        def _parse_base_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        base_url = _parse_base_url(d.pop("base_url", UNSET))

        enable_json_mode_if_requested = d.pop("enable_json_mode_if_requested", UNSET)

        model = d.pop("model", UNSET)

        def _parse_reasoning(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        reasoning = _parse_reasoning(d.pop("reasoning", UNSET))

        send_dashscope_header = d.pop("send_dashscope_header", UNSET)

        send_temperature = d.pop("send_temperature", UNSET)

        def _parse_term_api_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        term_api_key = _parse_term_api_key(d.pop("term_api_key", UNSET))

        def _parse_term_base_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        term_base_url = _parse_term_base_url(d.pop("term_base_url", UNSET))

        def _parse_term_model(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        term_model = _parse_term_model(d.pop("term_model", UNSET))

        def _parse_term_reasoning(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        term_reasoning = _parse_term_reasoning(d.pop("term_reasoning", UNSET))

        open_ai_request_args = cls(
            api_key=api_key,
            base_url=base_url,
            enable_json_mode_if_requested=enable_json_mode_if_requested,
            model=model,
            reasoning=reasoning,
            send_dashscope_header=send_dashscope_header,
            send_temperature=send_temperature,
            term_api_key=term_api_key,
            term_base_url=term_base_url,
            term_model=term_model,
            term_reasoning=term_reasoning,
        )

        return open_ai_request_args
