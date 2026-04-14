from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.glossary_entry_spec import GlossaryEntrySpec


T = TypeVar("T", bound="GlossarySpec")


@_attrs_define
class GlossarySpec:
    """User glossary inputs: CSV paths and/or inline entries.

    Attributes:
        csv_paths (list[str] | Unset):
        inline_entries (list[GlossaryEntrySpec] | Unset):
        inline_name (str | Unset):  Default: 'inline_glossary'.
    """

    csv_paths: list[str] | Unset = UNSET
    inline_entries: list[GlossaryEntrySpec] | Unset = UNSET
    inline_name: str | Unset = "inline_glossary"

    def to_dict(self) -> dict[str, Any]:
        csv_paths: list[str] | Unset = UNSET
        if not isinstance(self.csv_paths, Unset):
            csv_paths = self.csv_paths

        inline_entries: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.inline_entries, Unset):
            inline_entries = []
            for inline_entries_item_data in self.inline_entries:
                inline_entries_item = inline_entries_item_data.to_dict()
                inline_entries.append(inline_entries_item)

        inline_name = self.inline_name

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if csv_paths is not UNSET:
            field_dict["csv_paths"] = csv_paths
        if inline_entries is not UNSET:
            field_dict["inline_entries"] = inline_entries
        if inline_name is not UNSET:
            field_dict["inline_name"] = inline_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.glossary_entry_spec import GlossaryEntrySpec

        d = dict(src_dict)
        csv_paths = cast(list[str], d.pop("csv_paths", UNSET))

        _inline_entries = d.pop("inline_entries", UNSET)
        inline_entries: list[GlossaryEntrySpec] | Unset = UNSET
        if _inline_entries is not UNSET:
            inline_entries = []
            for inline_entries_item_data in _inline_entries:
                inline_entries_item = GlossaryEntrySpec.from_dict(inline_entries_item_data)

                inline_entries.append(inline_entries_item)

        inline_name = d.pop("inline_name", UNSET)

        glossary_spec = cls(
            csv_paths=csv_paths,
            inline_entries=inline_entries,
            inline_name=inline_name,
        )

        return glossary_spec
