from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.job_result_response_kind import JobResultResponseKind, check_job_result_response_kind
from ..models.job_result_response_state import JobResultResponseState, check_job_result_response_state
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.artifact_link import ArtifactLink
    from ..models.translation_error_payload import TranslationErrorPayload
    from ..models.translation_result import TranslationResult


T = TypeVar("T", bound="JobResultResponse")


@_attrs_define
class JobResultResponse:
    """
    Attributes:
        job_id (str):
        kind (JobResultResponseKind):
        state (JobResultResponseState):
        artifacts (list[ArtifactLink] | Unset):
        error (None | TranslationErrorPayload | Unset):
        schema_version (str | Unset):  Default: '1'.
        translation_result (None | TranslationResult | Unset):
    """

    job_id: str
    kind: JobResultResponseKind
    state: JobResultResponseState
    artifacts: list[ArtifactLink] | Unset = UNSET
    error: None | TranslationErrorPayload | Unset = UNSET
    schema_version: str | Unset = "1"
    translation_result: None | TranslationResult | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.translation_error_payload import TranslationErrorPayload
        from ..models.translation_result import TranslationResult

        job_id = self.job_id

        kind: str = self.kind

        state: str = self.state

        artifacts: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.artifacts, Unset):
            artifacts = []
            for artifacts_item_data in self.artifacts:
                artifacts_item = artifacts_item_data.to_dict()
                artifacts.append(artifacts_item)

        error: dict[str, Any] | None | Unset
        if isinstance(self.error, Unset):
            error = UNSET
        elif isinstance(self.error, TranslationErrorPayload):
            error = self.error.to_dict()
        else:
            error = self.error

        schema_version = self.schema_version

        translation_result: dict[str, Any] | None | Unset
        if isinstance(self.translation_result, Unset):
            translation_result = UNSET
        elif isinstance(self.translation_result, TranslationResult):
            translation_result = self.translation_result.to_dict()
        else:
            translation_result = self.translation_result

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "job_id": job_id,
                "kind": kind,
                "state": state,
            }
        )
        if artifacts is not UNSET:
            field_dict["artifacts"] = artifacts
        if error is not UNSET:
            field_dict["error"] = error
        if schema_version is not UNSET:
            field_dict["schema_version"] = schema_version
        if translation_result is not UNSET:
            field_dict["translation_result"] = translation_result

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.artifact_link import ArtifactLink
        from ..models.translation_error_payload import TranslationErrorPayload
        from ..models.translation_result import TranslationResult

        d = dict(src_dict)
        job_id = d.pop("job_id")

        kind = check_job_result_response_kind(d.pop("kind"))

        state = check_job_result_response_state(d.pop("state"))

        _artifacts = d.pop("artifacts", UNSET)
        artifacts: list[ArtifactLink] | Unset = UNSET
        if _artifacts is not UNSET:
            artifacts = []
            for artifacts_item_data in _artifacts:
                artifacts_item = ArtifactLink.from_dict(artifacts_item_data)

                artifacts.append(artifacts_item)

        def _parse_error(data: object) -> None | TranslationErrorPayload | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                error_type_0 = TranslationErrorPayload.from_dict(data)

                return error_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TranslationErrorPayload | Unset, data)

        error = _parse_error(d.pop("error", UNSET))

        schema_version = d.pop("schema_version", UNSET)

        def _parse_translation_result(data: object) -> None | TranslationResult | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                translation_result_type_0 = TranslationResult.from_dict(data)

                return translation_result_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TranslationResult | Unset, data)

        translation_result = _parse_translation_result(d.pop("translation_result", UNSET))

        job_result_response = cls(
            job_id=job_id,
            kind=kind,
            state=state,
            artifacts=artifacts,
            error=error,
            schema_version=schema_version,
            translation_result=translation_result,
        )

        return job_result_response
