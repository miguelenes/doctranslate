from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.asset_file_status import AssetFileStatus


T = TypeVar("T", bound="AssetStatusResponse")


@_attrs_define
class AssetStatusResponse:
    """
    Attributes:
        ready (bool):
        files (list[AssetFileStatus] | Unset):
        schema_version (str | Unset):  Default: '1'.
    """

    ready: bool
    files: list[AssetFileStatus] | Unset = UNSET
    schema_version: str | Unset = "1"

    def to_dict(self) -> dict[str, Any]:
        ready = self.ready

        files: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.files, Unset):
            files = []
            for files_item_data in self.files:
                files_item = files_item_data.to_dict()
                files.append(files_item)

        schema_version = self.schema_version

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "ready": ready,
            }
        )
        if files is not UNSET:
            field_dict["files"] = files
        if schema_version is not UNSET:
            field_dict["schema_version"] = schema_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.asset_file_status import AssetFileStatus

        d = dict(src_dict)
        ready = d.pop("ready")

        _files = d.pop("files", UNSET)
        files: list[AssetFileStatus] | Unset = UNSET
        if _files is not UNSET:
            files = []
            for files_item_data in _files:
                files_item = AssetFileStatus.from_dict(files_item_data)

                files.append(files_item)

        schema_version = d.pop("schema_version", UNSET)

        asset_status_response = cls(
            ready=ready,
            files=files,
            schema_version=schema_version,
        )

        return asset_status_response
