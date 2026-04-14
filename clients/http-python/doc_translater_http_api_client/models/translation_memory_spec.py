from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.translation_memory_spec_tm_mode import TranslationMemorySpecTmMode, check_translation_memory_spec_tm_mode
from ..models.translation_memory_spec_tm_scope import (
    TranslationMemorySpecTmScope,
    check_translation_memory_spec_tm_scope,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="TranslationMemorySpec")


@_attrs_define
class TranslationMemorySpec:
    """Translation memory options (maps to :class:`~doctranslate.format.pdf.translation_settings.TranslationSettings` TM
    fields).

        Attributes:
            tm_embedding_model (str | Unset):  Default: 'sentence-transformers/all-MiniLM-L6-v2'.
            tm_export_path (None | str | Unset):
            tm_fuzzy_min_score (float | Unset):  Default: 92.0.
            tm_import_path (None | str | Unset):
            tm_min_segment_chars (int | Unset):  Default: 12.
            tm_mode (TranslationMemorySpecTmMode | Unset):  Default: 'off'.
            tm_project_id (str | Unset):  Default: ''.
            tm_scope (TranslationMemorySpecTmScope | Unset):  Default: 'document'.
            tm_semantic_min_similarity (float | Unset):  Default: 0.9.
    """

    tm_embedding_model: str | Unset = "sentence-transformers/all-MiniLM-L6-v2"
    tm_export_path: None | str | Unset = UNSET
    tm_fuzzy_min_score: float | Unset = 92.0
    tm_import_path: None | str | Unset = UNSET
    tm_min_segment_chars: int | Unset = 12
    tm_mode: TranslationMemorySpecTmMode | Unset = "off"
    tm_project_id: str | Unset = ""
    tm_scope: TranslationMemorySpecTmScope | Unset = "document"
    tm_semantic_min_similarity: float | Unset = 0.9

    def to_dict(self) -> dict[str, Any]:
        tm_embedding_model = self.tm_embedding_model

        tm_export_path: None | str | Unset
        if isinstance(self.tm_export_path, Unset):
            tm_export_path = UNSET
        else:
            tm_export_path = self.tm_export_path

        tm_fuzzy_min_score = self.tm_fuzzy_min_score

        tm_import_path: None | str | Unset
        if isinstance(self.tm_import_path, Unset):
            tm_import_path = UNSET
        else:
            tm_import_path = self.tm_import_path

        tm_min_segment_chars = self.tm_min_segment_chars

        tm_mode: str | Unset = UNSET
        if not isinstance(self.tm_mode, Unset):
            tm_mode = self.tm_mode

        tm_project_id = self.tm_project_id

        tm_scope: str | Unset = UNSET
        if not isinstance(self.tm_scope, Unset):
            tm_scope = self.tm_scope

        tm_semantic_min_similarity = self.tm_semantic_min_similarity

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if tm_embedding_model is not UNSET:
            field_dict["tm_embedding_model"] = tm_embedding_model
        if tm_export_path is not UNSET:
            field_dict["tm_export_path"] = tm_export_path
        if tm_fuzzy_min_score is not UNSET:
            field_dict["tm_fuzzy_min_score"] = tm_fuzzy_min_score
        if tm_import_path is not UNSET:
            field_dict["tm_import_path"] = tm_import_path
        if tm_min_segment_chars is not UNSET:
            field_dict["tm_min_segment_chars"] = tm_min_segment_chars
        if tm_mode is not UNSET:
            field_dict["tm_mode"] = tm_mode
        if tm_project_id is not UNSET:
            field_dict["tm_project_id"] = tm_project_id
        if tm_scope is not UNSET:
            field_dict["tm_scope"] = tm_scope
        if tm_semantic_min_similarity is not UNSET:
            field_dict["tm_semantic_min_similarity"] = tm_semantic_min_similarity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        tm_embedding_model = d.pop("tm_embedding_model", UNSET)

        def _parse_tm_export_path(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tm_export_path = _parse_tm_export_path(d.pop("tm_export_path", UNSET))

        tm_fuzzy_min_score = d.pop("tm_fuzzy_min_score", UNSET)

        def _parse_tm_import_path(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tm_import_path = _parse_tm_import_path(d.pop("tm_import_path", UNSET))

        tm_min_segment_chars = d.pop("tm_min_segment_chars", UNSET)

        _tm_mode = d.pop("tm_mode", UNSET)
        tm_mode: TranslationMemorySpecTmMode | Unset
        if isinstance(_tm_mode, Unset):
            tm_mode = UNSET
        else:
            tm_mode = check_translation_memory_spec_tm_mode(_tm_mode)

        tm_project_id = d.pop("tm_project_id", UNSET)

        _tm_scope = d.pop("tm_scope", UNSET)
        tm_scope: TranslationMemorySpecTmScope | Unset
        if isinstance(_tm_scope, Unset):
            tm_scope = UNSET
        else:
            tm_scope = check_translation_memory_spec_tm_scope(_tm_scope)

        tm_semantic_min_similarity = d.pop("tm_semantic_min_similarity", UNSET)

        translation_memory_spec = cls(
            tm_embedding_model=tm_embedding_model,
            tm_export_path=tm_export_path,
            tm_fuzzy_min_score=tm_fuzzy_min_score,
            tm_import_path=tm_import_path,
            tm_min_segment_chars=tm_min_segment_chars,
            tm_mode=tm_mode,
            tm_project_id=tm_project_id,
            tm_scope=tm_scope,
            tm_semantic_min_similarity=tm_semantic_min_similarity,
        )

        return translation_memory_spec
