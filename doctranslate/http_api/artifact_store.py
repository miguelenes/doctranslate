"""Artifact/blob storage for HTTP API jobs (data plane)."""

from __future__ import annotations

import asyncio
import logging
import shutil
from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import Any
from typing import BinaryIO

import fsspec
import fsspec.core

from doctranslate.http_api.storage import JobPaths
from doctranslate.schemas.enums import ArtifactKind
from doctranslate.schemas.public_api import ArtifactDescriptor
from doctranslate.schemas.public_api import TranslationResult

logger = logging.getLogger(__name__)


class ArtifactStore(ABC):
    """Store inputs and outputs for translation jobs."""

    @abstractmethod
    def job_paths(self, job_id: str) -> JobPaths:
        """Layout for the job workspace (local paths for the PDF engine)."""

    @abstractmethod
    def ensure_workspace(self, job_id: str) -> JobPaths:
        """Create input/work/output directories if needed."""

    @abstractmethod
    async def save_uploaded_input(
        self,
        job_id: str,
        preferred_filename: str | None,
        max_bytes: int,
        read_chunk: Any,
    ) -> Path:
        """Stream upload to the job input area; return local path for ``TranslationRequest``."""

    @abstractmethod
    def local_output_dir(self, job_id: str) -> Path:
        """Directory the translation engine must write into."""

    @abstractmethod
    async def finalize_translation_result(
        self,
        job_id: str,
        result: TranslationResult,
    ) -> TranslationResult:
        """Optionally upload artifacts and normalize ``ArtifactDescriptor.path`` values."""

    @abstractmethod
    def resolve_artifact_for_download(
        self,
        job_id: str,
        kind: ArtifactKind,
        artifact: ArtifactDescriptor,
    ) -> tuple[str, dict[str, Any]]:
        """
        Resolve how to serve ``artifact``.

        Returns ``(mode, payload)`` where ``mode`` is ``path`` or ``fsspec``,
        and ``payload`` holds ``path`` / ``url`` / ``filename`` keys.
        """

    @abstractmethod
    async def delete_job_prefix(self, job_id: str) -> None:
        """Remove all blobs for ``job_id`` (best-effort)."""

    def fsspec_read_options(self) -> dict[str, Any]:
        """Extra kwargs for ``fsspec.open(..., "rb", **opts)`` when reading remote artifacts."""
        return {}

    def delegated_download_url(
        self, artifact: ArtifactDescriptor, expires_seconds: int
    ) -> str | None:
        """Optional presigned URL; default no delegation."""
        return None


class LocalFilesystemArtifactStore(ArtifactStore):
    """Local disk under ``data_root`` (default OSS backend)."""

    def __init__(self, data_root: Path) -> None:
        self._data_root = data_root.expanduser()

    def job_paths(self, job_id: str) -> JobPaths:
        return JobPaths.under(self._data_root, job_id)

    def ensure_workspace(self, job_id: str) -> JobPaths:
        paths = self.job_paths(job_id)
        paths.mkdirs()
        return paths

    async def save_uploaded_input(
        self,
        job_id: str,
        preferred_filename: str | None,
        max_bytes: int,
        read_chunk: Any,
    ) -> Path:
        paths = self.ensure_workspace(job_id)
        name = preferred_filename or "input.pdf"
        if not name.lower().endswith(".pdf"):
            name = f"{Path(name).stem}.pdf"
        dest = paths.input_dir / name
        size = 0
        with dest.open("wb") as out:
            while True:
                chunk = await read_chunk(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    msg = f"Upload exceeds max_upload_bytes={max_bytes}"
                    raise ValueError(msg)
                out.write(chunk)
        return dest.resolve()

    def local_output_dir(self, job_id: str) -> Path:
        return self.job_paths(job_id).output_dir.resolve()

    async def finalize_translation_result(
        self,
        job_id: str,
        result: TranslationResult,
    ) -> TranslationResult:
        return result

    def resolve_artifact_for_download(
        self,
        job_id: str,
        kind: ArtifactKind,
        artifact: ArtifactDescriptor,
    ) -> tuple[str, dict[str, Any]]:
        paths = self.job_paths(job_id)
        p = Path(artifact.path)
        if artifact.path.startswith(f"file://{job_id}/"):
            rel = artifact.path.removeprefix(f"file://{job_id}/").lstrip("/")
            p = (paths.root / rel).resolve()
        elif artifact.path.startswith("file:///"):
            p = Path(artifact.path.replace("file://", "", 1))
        elif not p.is_file():
            rel = artifact.path.removeprefix(f"{job_id}/").lstrip("/")
            candidate = (paths.root / rel).resolve()
            if candidate.is_file():
                p = candidate
        return ("path", {"path": p, "filename": p.name})

    async def delete_job_prefix(self, job_id: str) -> None:
        root = self.job_paths(job_id).root

        def _rm() -> None:
            shutil.rmtree(root, ignore_errors=True)

        await asyncio.to_thread(_rm)

    def fsspec_read_options(self) -> dict[str, Any]:
        return {}


class FsspecRemoteArtifactStore(ArtifactStore):
    """
    Stage translation on local disk under ``data_root``, mirror blobs to ``remote_root``.

    ``remote_root`` is an fsspec URL, e.g. ``file:///tmp/remote`` (tests) or ``s3://bucket/prefix``
    (requires ``s3fs``).
    """

    def __init__(
        self,
        *,
        data_root: Path,
        remote_root: str,
        storage_options: dict[str, Any] | None = None,
    ) -> None:
        self._data_root = data_root.expanduser()
        self._remote_root = remote_root.rstrip("/")
        self._storage_options = storage_options or {}

    def fsspec_read_options(self) -> dict[str, Any]:
        return dict(self._storage_options)

    def job_paths(self, job_id: str) -> JobPaths:
        return JobPaths.under(self._data_root, job_id)

    def ensure_workspace(self, job_id: str) -> JobPaths:
        paths = self.job_paths(job_id)
        paths.mkdirs()
        return paths

    def _remote_url(self, *segments: str) -> str:
        return self._remote_root + "/" + "/".join(segments)

    async def save_uploaded_input(
        self,
        job_id: str,
        preferred_filename: str | None,
        max_bytes: int,
        read_chunk: Any,
    ) -> Path:
        paths = self.ensure_workspace(job_id)
        name = preferred_filename or "input.pdf"
        if not name.lower().endswith(".pdf"):
            name = f"{Path(name).stem}.pdf"
        dest = paths.input_dir / name
        size = 0
        with dest.open("wb") as out:
            while True:
                chunk = await read_chunk(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    msg = f"Upload exceeds max_upload_bytes={max_bytes}"
                    raise ValueError(msg)
                out.write(chunk)
        resolved = dest.resolve()
        rurl = self._remote_url("jobs", job_id, "input", resolved.name)

        def _mirror() -> None:
            with resolved.open("rb") as src:
                with fsspec.open(rurl, "wb", **self._storage_options) as dst:
                    shutil.copyfileobj(src, dst)

        await asyncio.to_thread(_mirror)
        return resolved

    def local_output_dir(self, job_id: str) -> Path:
        return self.job_paths(job_id).output_dir.resolve()

    async def finalize_translation_result(
        self,
        job_id: str,
        result: TranslationResult,
    ) -> TranslationResult:
        paths = self.job_paths(job_id)
        out_root = paths.output_dir.resolve()

        def _upload_and_map() -> list[ArtifactDescriptor]:
            mapped: list[ArtifactDescriptor] = []
            for item in result.artifacts.items:
                p = Path(item.path)
                if not p.is_file():
                    mapped.append(item)
                    continue
                try:
                    rel = p.resolve().relative_to(out_root)
                except ValueError:
                    rel = Path(p.name)
                rurl = self._remote_url("jobs", job_id, "output", rel.as_posix())

                with p.open("rb") as src:
                    with fsspec.open(rurl, "wb", **self._storage_options) as dst:
                        shutil.copyfileobj(src, dst)
                mapped.append(item.model_copy(update={"path": rurl}))
            return mapped

        new_items = await asyncio.to_thread(_upload_and_map)
        return result.model_copy(
            update={"artifacts": type(result.artifacts)(items=new_items)},
        )

    def resolve_artifact_for_download(
        self,
        job_id: str,
        kind: ArtifactKind,
        artifact: ArtifactDescriptor,
    ) -> tuple[str, dict[str, Any]]:
        path_str = artifact.path
        if (
            path_str.startswith("s3://")
            or path_str.startswith("gs://")
            or path_str.startswith(
                "gcs://",
            )
        ):
            normalized = path_str.replace("gcs://", "gs://", 1)
            return (
                "fsspec",
                {"url": normalized, "filename": Path(path_str.split("/")[-1]).name},
            )
        p = Path(path_str)
        return ("path", {"path": p, "filename": p.name})

    async def delete_job_prefix(self, job_id: str) -> None:
        target = self._remote_url("jobs", job_id)

        def _rm_remote() -> None:
            try:
                fs, tok = fsspec.core.url_to_fs(target, **self._storage_options)
            except Exception:
                logger.exception("Failed to resolve remote URL for cleanup: %s", target)
                return
            try:
                if fs.exists(tok):
                    fs.rm(tok, recursive=True)
            except Exception:
                logger.exception("Remote cleanup failed for %s", target)

        await asyncio.to_thread(_rm_remote)
        await LocalFilesystemArtifactStore(self._data_root).delete_job_prefix(job_id)


def open_fsspec_read(
    url: str, storage_options: dict[str, Any] | None = None
) -> BinaryIO:
    """Open remote object for reading (blocking)."""
    opts = storage_options or {}
    return fsspec.open(url, "rb", **opts).__enter__()
