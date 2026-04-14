from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.input_file_inspection import InputFileInspection


T = TypeVar("T", bound="InputInspectionResult")


@_attrs_define
class InputInspectionResult:
    """Result of :func:`doctranslate.api.inspect_input`.

    Attributes:
        files (list[InputFileInspection] | Unset):
        schema_version (str | Unset):  Default: '1'.
    """

    files: list[InputFileInspection] | Unset = UNSET
    schema_version: str | Unset = "1"

    def to_dict(self) -> dict[str, Any]:
        files: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.files, Unset):
            files = []
            for files_item_data in self.files:
                files_item = files_item_data.to_dict()
                files.append(files_item)

        schema_version = self.schema_version

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if files is not UNSET:
            field_dict["files"] = files
        if schema_version is not UNSET:
            field_dict["schema_version"] = schema_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.input_file_inspection import InputFileInspection

        d = dict(src_dict)
        _files = d.pop("files", UNSET)
        files: list[InputFileInspection] | Unset = UNSET
        if _files is not UNSET:
            files = []
            for files_item_data in _files:
                files_item = InputFileInspection.from_dict(files_item_data)

                files.append(files_item)

        schema_version = d.pop("schema_version", UNSET)

        input_inspection_result = cls(
            files=files,
            schema_version=schema_version,
        )

        return input_inspection_result
