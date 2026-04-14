from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.artifact_kind import ArtifactKind, check_artifact_kind
from ..types import UNSET, Unset

T = TypeVar("T", bound="ArtifactDescriptor")


@_attrs_define
class ArtifactDescriptor:
    """One output artifact.

    Attributes:
        kind (ArtifactKind): Kinds of outputs produced by a translation job.
        path (str):
        media_type (None | str | Unset):
        schema_version (str | Unset):  Default: '1'.
        sha256 (None | str | Unset):
        size_bytes (int | None | Unset):
    """

    kind: ArtifactKind
    path: str
    media_type: None | str | Unset = UNSET
    schema_version: str | Unset = "1"
    sha256: None | str | Unset = UNSET
    size_bytes: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        kind: str = self.kind

        path = self.path

        media_type: None | str | Unset
        if isinstance(self.media_type, Unset):
            media_type = UNSET
        else:
            media_type = self.media_type

        schema_version = self.schema_version

        sha256: None | str | Unset
        if isinstance(self.sha256, Unset):
            sha256 = UNSET
        else:
            sha256 = self.sha256

        size_bytes: int | None | Unset
        if isinstance(self.size_bytes, Unset):
            size_bytes = UNSET
        else:
            size_bytes = self.size_bytes

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "kind": kind,
                "path": path,
            }
        )
        if media_type is not UNSET:
            field_dict["media_type"] = media_type
        if schema_version is not UNSET:
            field_dict["schema_version"] = schema_version
        if sha256 is not UNSET:
            field_dict["sha256"] = sha256
        if size_bytes is not UNSET:
            field_dict["size_bytes"] = size_bytes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        kind = check_artifact_kind(d.pop("kind"))

        path = d.pop("path")

        def _parse_media_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        media_type = _parse_media_type(d.pop("media_type", UNSET))

        schema_version = d.pop("schema_version", UNSET)

        def _parse_sha256(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        sha256 = _parse_sha256(d.pop("sha256", UNSET))

        def _parse_size_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        size_bytes = _parse_size_bytes(d.pop("size_bytes", UNSET))

        artifact_descriptor = cls(
            kind=kind,
            path=path,
            media_type=media_type,
            schema_version=schema_version,
            sha256=sha256,
            size_bytes=size_bytes,
        )

        return artifact_descriptor
