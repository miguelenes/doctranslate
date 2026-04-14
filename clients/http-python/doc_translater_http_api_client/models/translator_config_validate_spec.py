from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.translator_config_validate_spec_mode import (
    TranslatorConfigValidateSpecMode,
    check_translator_config_validate_spec_mode,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.translator_config_validate_spec_local_cli_type_0 import TranslatorConfigValidateSpecLocalCliType0


T = TypeVar("T", bound="TranslatorConfigValidateSpec")


@_attrs_define
class TranslatorConfigValidateSpec:
    """Optional nested validation for router/local TOML (mirrors CLI intent).

    Attributes:
        config_path (str):
        mode (TranslatorConfigValidateSpecMode):
        local_cli (None | TranslatorConfigValidateSpecLocalCliType0 | Unset):
        metrics_json_path (None | str | Unset):
        metrics_output (None | str | Unset):
        routing_profile (None | str | Unset):
        routing_strategy (None | str | Unset):
        term_extraction_profile (None | str | Unset):
    """

    config_path: str
    mode: TranslatorConfigValidateSpecMode
    local_cli: None | TranslatorConfigValidateSpecLocalCliType0 | Unset = UNSET
    metrics_json_path: None | str | Unset = UNSET
    metrics_output: None | str | Unset = UNSET
    routing_profile: None | str | Unset = UNSET
    routing_strategy: None | str | Unset = UNSET
    term_extraction_profile: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.translator_config_validate_spec_local_cli_type_0 import TranslatorConfigValidateSpecLocalCliType0

        config_path = self.config_path

        mode: str = self.mode

        local_cli: dict[str, Any] | None | Unset
        if isinstance(self.local_cli, Unset):
            local_cli = UNSET
        elif isinstance(self.local_cli, TranslatorConfigValidateSpecLocalCliType0):
            local_cli = self.local_cli.to_dict()
        else:
            local_cli = self.local_cli

        metrics_json_path: None | str | Unset
        if isinstance(self.metrics_json_path, Unset):
            metrics_json_path = UNSET
        else:
            metrics_json_path = self.metrics_json_path

        metrics_output: None | str | Unset
        if isinstance(self.metrics_output, Unset):
            metrics_output = UNSET
        else:
            metrics_output = self.metrics_output

        routing_profile: None | str | Unset
        if isinstance(self.routing_profile, Unset):
            routing_profile = UNSET
        else:
            routing_profile = self.routing_profile

        routing_strategy: None | str | Unset
        if isinstance(self.routing_strategy, Unset):
            routing_strategy = UNSET
        else:
            routing_strategy = self.routing_strategy

        term_extraction_profile: None | str | Unset
        if isinstance(self.term_extraction_profile, Unset):
            term_extraction_profile = UNSET
        else:
            term_extraction_profile = self.term_extraction_profile

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "config_path": config_path,
                "mode": mode,
            }
        )
        if local_cli is not UNSET:
            field_dict["local_cli"] = local_cli
        if metrics_json_path is not UNSET:
            field_dict["metrics_json_path"] = metrics_json_path
        if metrics_output is not UNSET:
            field_dict["metrics_output"] = metrics_output
        if routing_profile is not UNSET:
            field_dict["routing_profile"] = routing_profile
        if routing_strategy is not UNSET:
            field_dict["routing_strategy"] = routing_strategy
        if term_extraction_profile is not UNSET:
            field_dict["term_extraction_profile"] = term_extraction_profile

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.translator_config_validate_spec_local_cli_type_0 import TranslatorConfigValidateSpecLocalCliType0

        d = dict(src_dict)
        config_path = d.pop("config_path")

        mode = check_translator_config_validate_spec_mode(d.pop("mode"))

        def _parse_local_cli(data: object) -> None | TranslatorConfigValidateSpecLocalCliType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                local_cli_type_0 = TranslatorConfigValidateSpecLocalCliType0.from_dict(data)

                return local_cli_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TranslatorConfigValidateSpecLocalCliType0 | Unset, data)

        local_cli = _parse_local_cli(d.pop("local_cli", UNSET))

        def _parse_metrics_json_path(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        metrics_json_path = _parse_metrics_json_path(d.pop("metrics_json_path", UNSET))

        def _parse_metrics_output(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        metrics_output = _parse_metrics_output(d.pop("metrics_output", UNSET))

        def _parse_routing_profile(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        routing_profile = _parse_routing_profile(d.pop("routing_profile", UNSET))

        def _parse_routing_strategy(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        routing_strategy = _parse_routing_strategy(d.pop("routing_strategy", UNSET))

        def _parse_term_extraction_profile(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        term_extraction_profile = _parse_term_extraction_profile(d.pop("term_extraction_profile", UNSET))

        translator_config_validate_spec = cls(
            config_path=config_path,
            mode=mode,
            local_cli=local_cli,
            metrics_json_path=metrics_json_path,
            metrics_output=metrics_output,
            routing_profile=routing_profile,
            routing_strategy=routing_strategy,
            term_extraction_profile=term_extraction_profile,
        )

        return translator_config_validate_spec
