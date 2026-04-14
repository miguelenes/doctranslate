"""Construct artifact and metadata stores from settings."""

from __future__ import annotations

from doctranslate.http_api.artifact_store import ArtifactStore
from doctranslate.http_api.artifact_store import FsspecRemoteArtifactStore
from doctranslate.http_api.artifact_store import LocalFilesystemArtifactStore
from doctranslate.http_api.metadata_store.sqlite import SqliteJobMetadataStore
from doctranslate.http_api.settings import ApiSettings


def build_artifact_store(settings: ApiSettings) -> ArtifactStore:
    if settings.artifact_storage == "remote" and settings.artifact_remote_root.strip():
        opts = settings.parsed_fsspec_storage_options()
        return FsspecRemoteArtifactStore(
            data_root=settings.data_root,
            remote_root=settings.artifact_remote_root.strip(),
            storage_options=opts,
        )
    return LocalFilesystemArtifactStore(settings.data_root)


def build_metadata_store(settings: ApiSettings) -> SqliteJobMetadataStore:
    path = settings.metadata_sqlite_path or (
        settings.data_root / "http_api_metadata.db"
    )
    return SqliteJobMetadataStore(path.expanduser())
