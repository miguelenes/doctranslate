from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.artifact_manifest import ArtifactManifest
    from ..models.translation_summary import TranslationSummary


T = TypeVar("T", bound="TranslationResult")


@_attrs_define
class TranslationResult:
    """Stable completion payload (replaces ad hoc TranslateResult for embedders).

    Attributes:
        artifacts (ArtifactManifest): All artifacts from a completed job.
        summary (TranslationSummary): High-level run metrics.
        schema_version (str | Unset):  Default: '1'.
        warnings (list[str] | Unset):
    """

    artifacts: ArtifactManifest
    summary: TranslationSummary
    schema_version: str | Unset = "1"
    warnings: list[str] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        artifacts = self.artifacts.to_dict()

        summary = self.summary.to_dict()

        schema_version = self.schema_version

        warnings: list[str] | Unset = UNSET
        if not isinstance(self.warnings, Unset):
            warnings = self.warnings

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "artifacts": artifacts,
                "summary": summary,
            }
        )
        if schema_version is not UNSET:
            field_dict["schema_version"] = schema_version
        if warnings is not UNSET:
            field_dict["warnings"] = warnings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.artifact_manifest import ArtifactManifest
        from ..models.translation_summary import TranslationSummary

        d = dict(src_dict)
        artifacts = ArtifactManifest.from_dict(d.pop("artifacts"))

        summary = TranslationSummary.from_dict(d.pop("summary"))

        schema_version = d.pop("schema_version", UNSET)

        warnings = cast(list[str], d.pop("warnings", UNSET))

        translation_result = cls(
            artifacts=artifacts,
            summary=summary,
            schema_version=schema_version,
            warnings=warnings,
        )

        return translation_result
