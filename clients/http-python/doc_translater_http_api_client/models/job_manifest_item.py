from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.artifact_kind import ArtifactKind, check_artifact_kind
from ..types import UNSET, Unset

T = TypeVar("T", bound="JobManifestItem")


@_attrs_define
class JobManifestItem:
    """
    Attributes:
        download_url (str):
        kind (ArtifactKind): Kinds of outputs produced by a translation job.
        path (str):
        download_expires_in_seconds (int | None | Unset):
        filename (None | str | Unset):
        media_type (None | str | Unset):
        sha256 (None | str | Unset):
        size_bytes (int | None | Unset):
    """

    download_url: str
    kind: ArtifactKind
    path: str
    download_expires_in_seconds: int | None | Unset = UNSET
    filename: None | str | Unset = UNSET
    media_type: None | str | Unset = UNSET
    sha256: None | str | Unset = UNSET
    size_bytes: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        download_url = self.download_url

        kind: str = self.kind

        path = self.path

        download_expires_in_seconds: int | None | Unset
        if isinstance(self.download_expires_in_seconds, Unset):
            download_expires_in_seconds = UNSET
        else:
            download_expires_in_seconds = self.download_expires_in_seconds

        filename: None | str | Unset
        if isinstance(self.filename, Unset):
            filename = UNSET
        else:
            filename = self.filename

        media_type: None | str | Unset
        if isinstance(self.media_type, Unset):
            media_type = UNSET
        else:
            media_type = self.media_type

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
                "download_url": download_url,
                "kind": kind,
                "path": path,
            }
        )
        if download_expires_in_seconds is not UNSET:
            field_dict["download_expires_in_seconds"] = download_expires_in_seconds
        if filename is not UNSET:
            field_dict["filename"] = filename
        if media_type is not UNSET:
            field_dict["media_type"] = media_type
        if sha256 is not UNSET:
            field_dict["sha256"] = sha256
        if size_bytes is not UNSET:
            field_dict["size_bytes"] = size_bytes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        download_url = d.pop("download_url")

        kind = check_artifact_kind(d.pop("kind"))

        path = d.pop("path")

        def _parse_download_expires_in_seconds(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        download_expires_in_seconds = _parse_download_expires_in_seconds(d.pop("download_expires_in_seconds", UNSET))

        def _parse_filename(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        filename = _parse_filename(d.pop("filename", UNSET))

        def _parse_media_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        media_type = _parse_media_type(d.pop("media_type", UNSET))

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

        job_manifest_item = cls(
            download_url=download_url,
            kind=kind,
            path=path,
            download_expires_in_seconds=download_expires_in_seconds,
            filename=filename,
            media_type=media_type,
            sha256=sha256,
            size_bytes=size_bytes,
        )

        return job_manifest_item
