from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.translator_mode import TranslatorMode, check_translator_mode
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.open_ai_request_args import OpenAIRequestArgs
    from ..models.translator_request_config_cli_router_overrides_type_0 import (
        TranslatorRequestConfigCliRouterOverridesType0,
    )
    from ..models.translator_request_config_local_cli_type_0 import TranslatorRequestConfigLocalCliType0


T = TypeVar("T", bound="TranslatorRequestConfig")


@_attrs_define
class TranslatorRequestConfig:
    """How to build translators for a job.

    Attributes:
        cli_router_overrides (None | TranslatorRequestConfigCliRouterOverridesType0 | Unset):
        config_path (None | str | Unset):
        ignore_cache (bool | Unset):  Default: False.
        local_cli (None | TranslatorRequestConfigLocalCliType0 | Unset):
        mode (TranslatorMode | Unset): How translators are constructed for a job.
        openai (None | OpenAIRequestArgs | Unset):
    """

    cli_router_overrides: None | TranslatorRequestConfigCliRouterOverridesType0 | Unset = UNSET
    config_path: None | str | Unset = UNSET
    ignore_cache: bool | Unset = False
    local_cli: None | TranslatorRequestConfigLocalCliType0 | Unset = UNSET
    mode: TranslatorMode | Unset = UNSET
    openai: None | OpenAIRequestArgs | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.open_ai_request_args import OpenAIRequestArgs
        from ..models.translator_request_config_cli_router_overrides_type_0 import (
            TranslatorRequestConfigCliRouterOverridesType0,
        )
        from ..models.translator_request_config_local_cli_type_0 import TranslatorRequestConfigLocalCliType0

        cli_router_overrides: dict[str, Any] | None | Unset
        if isinstance(self.cli_router_overrides, Unset):
            cli_router_overrides = UNSET
        elif isinstance(self.cli_router_overrides, TranslatorRequestConfigCliRouterOverridesType0):
            cli_router_overrides = self.cli_router_overrides.to_dict()
        else:
            cli_router_overrides = self.cli_router_overrides

        config_path: None | str | Unset
        if isinstance(self.config_path, Unset):
            config_path = UNSET
        else:
            config_path = self.config_path

        ignore_cache = self.ignore_cache

        local_cli: dict[str, Any] | None | Unset
        if isinstance(self.local_cli, Unset):
            local_cli = UNSET
        elif isinstance(self.local_cli, TranslatorRequestConfigLocalCliType0):
            local_cli = self.local_cli.to_dict()
        else:
            local_cli = self.local_cli

        mode: str | Unset = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode

        openai: dict[str, Any] | None | Unset
        if isinstance(self.openai, Unset):
            openai = UNSET
        elif isinstance(self.openai, OpenAIRequestArgs):
            openai = self.openai.to_dict()
        else:
            openai = self.openai

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if cli_router_overrides is not UNSET:
            field_dict["cli_router_overrides"] = cli_router_overrides
        if config_path is not UNSET:
            field_dict["config_path"] = config_path
        if ignore_cache is not UNSET:
            field_dict["ignore_cache"] = ignore_cache
        if local_cli is not UNSET:
            field_dict["local_cli"] = local_cli
        if mode is not UNSET:
            field_dict["mode"] = mode
        if openai is not UNSET:
            field_dict["openai"] = openai

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.open_ai_request_args import OpenAIRequestArgs
        from ..models.translator_request_config_cli_router_overrides_type_0 import (
            TranslatorRequestConfigCliRouterOverridesType0,
        )
        from ..models.translator_request_config_local_cli_type_0 import TranslatorRequestConfigLocalCliType0

        d = dict(src_dict)

        def _parse_cli_router_overrides(data: object) -> None | TranslatorRequestConfigCliRouterOverridesType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                cli_router_overrides_type_0 = TranslatorRequestConfigCliRouterOverridesType0.from_dict(data)

                return cli_router_overrides_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TranslatorRequestConfigCliRouterOverridesType0 | Unset, data)

        cli_router_overrides = _parse_cli_router_overrides(d.pop("cli_router_overrides", UNSET))

        def _parse_config_path(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        config_path = _parse_config_path(d.pop("config_path", UNSET))

        ignore_cache = d.pop("ignore_cache", UNSET)

        def _parse_local_cli(data: object) -> None | TranslatorRequestConfigLocalCliType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                local_cli_type_0 = TranslatorRequestConfigLocalCliType0.from_dict(data)

                return local_cli_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TranslatorRequestConfigLocalCliType0 | Unset, data)

        local_cli = _parse_local_cli(d.pop("local_cli", UNSET))

        _mode = d.pop("mode", UNSET)
        mode: TranslatorMode | Unset
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = check_translator_mode(_mode)

        def _parse_openai(data: object) -> None | OpenAIRequestArgs | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                openai_type_0 = OpenAIRequestArgs.from_dict(data)

                return openai_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | OpenAIRequestArgs | Unset, data)

        openai = _parse_openai(d.pop("openai", UNSET))

        translator_request_config = cls(
            cli_router_overrides=cli_router_overrides,
            config_path=config_path,
            ignore_cache=ignore_cache,
            local_cli=local_cli,
            mode=mode,
            openai=openai,
        )

        return translator_request_config
