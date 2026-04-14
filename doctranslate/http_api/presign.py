"""Optional presigned download URLs for object storage."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def presign_s3_get_url(url: str, *, expires_in: int = 3600) -> str | None:
    """Return a presigned GET URL for ``s3://bucket/key`` or ``None`` if unavailable."""
    try:
        import boto3  # noqa: PLC0415
    except ImportError:
        logger.debug("boto3 not installed; cannot presign S3 URL")
        return None
    if not url.startswith("s3://"):
        return None
    parsed = urlparse(url)
    if parsed.scheme != "s3" or not parsed.netloc or not parsed.path:
        return None
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    if not key:
        return None
    try:
        client = boto3.client("s3")
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
    except Exception:
        logger.exception("Failed to presign S3 URL")
        return None


def presign_gcs_url(url: str, *, expires_in: int = 3600) -> str | None:
    """Return a signed URL for ``gs://bucket/object`` using gcsfs, or ``None``."""
    if not (url.startswith("gs://") or url.startswith("gcs://")):
        return None
    normalized = url.replace("gcs://", "gs://", 1)
    try:
        from gcsfs import GCSFileSystem  # noqa: PLC0415
    except ImportError:
        logger.debug("gcsfs not installed; cannot sign GCS URL")
        return None
    try:
        fs = GCSFileSystem()
        path = normalized.removeprefix("gs://")
        return fs.sign(path, expiration=expires_in)
    except Exception:
        logger.exception("Failed to sign GCS URL")
        return None
