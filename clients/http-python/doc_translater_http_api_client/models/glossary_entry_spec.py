from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="GlossaryEntrySpec")


@_attrs_define
class GlossaryEntrySpec:
    """Single glossary row (optional inline glossaries).

    Attributes:
        source (str):
        target (str):
        target_language (None | str | Unset): Optional tgt_lng column equivalent for filtering.
    """

    source: str
    target: str
    target_language: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        source = self.source

        target = self.target

        target_language: None | str | Unset
        if isinstance(self.target_language, Unset):
            target_language = UNSET
        else:
            target_language = self.target_language

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "source": source,
                "target": target,
            }
        )
        if target_language is not UNSET:
            field_dict["target_language"] = target_language

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        source = d.pop("source")

        target = d.pop("target")

        def _parse_target_language(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        target_language = _parse_target_language(d.pop("target_language", UNSET))

        glossary_entry_spec = cls(
            source=source,
            target=target,
            target_language=target_language,
        )

        return glossary_entry_spec
