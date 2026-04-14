from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.job_status_response_kind import JobStatusResponseKind, check_job_status_response_kind
from ..models.job_status_response_state import JobStatusResponseState, check_job_status_response_state
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.progress_end_event import ProgressEndEvent
    from ..models.progress_start_event import ProgressStartEvent
    from ..models.progress_update_event import ProgressUpdateEvent
    from ..models.stage_summary_event import StageSummaryEvent
    from ..models.translation_error_event import TranslationErrorEvent
    from ..models.translation_error_payload import TranslationErrorPayload
    from ..models.translation_finished_event import TranslationFinishedEvent


T = TypeVar("T", bound="JobStatusResponse")


@_attrs_define
class JobStatusResponse:
    """
    Attributes:
        created_at (datetime.datetime):
        job_id (str):
        kind (JobStatusResponseKind):
        state (JobStatusResponseState):
        updated_at (datetime.datetime):
        error (None | TranslationErrorPayload | Unset):
        message (None | str | Unset):
        progress (None | ProgressEndEvent | ProgressStartEvent | ProgressUpdateEvent | StageSummaryEvent |
            TranslationErrorEvent | TranslationFinishedEvent | Unset):
        progress_seq (int | Unset):  Default: 0.
        schema_version (str | Unset):  Default: '1'.
    """

    created_at: datetime.datetime
    job_id: str
    kind: JobStatusResponseKind
    state: JobStatusResponseState
    updated_at: datetime.datetime
    error: None | TranslationErrorPayload | Unset = UNSET
    message: None | str | Unset = UNSET
    progress: (
        None
        | ProgressEndEvent
        | ProgressStartEvent
        | ProgressUpdateEvent
        | StageSummaryEvent
        | TranslationErrorEvent
        | TranslationFinishedEvent
        | Unset
    ) = UNSET
    progress_seq: int | Unset = 0
    schema_version: str | Unset = "1"

    def to_dict(self) -> dict[str, Any]:
        from ..models.progress_end_event import ProgressEndEvent
        from ..models.progress_start_event import ProgressStartEvent
        from ..models.progress_update_event import ProgressUpdateEvent
        from ..models.stage_summary_event import StageSummaryEvent
        from ..models.translation_error_event import TranslationErrorEvent
        from ..models.translation_error_payload import TranslationErrorPayload
        from ..models.translation_finished_event import TranslationFinishedEvent

        created_at = self.created_at.isoformat()

        job_id = self.job_id

        kind: str = self.kind

        state: str = self.state

        updated_at = self.updated_at.isoformat()

        error: dict[str, Any] | None | Unset
        if isinstance(self.error, Unset):
            error = UNSET
        elif isinstance(self.error, TranslationErrorPayload):
            error = self.error.to_dict()
        else:
            error = self.error

        message: None | str | Unset
        if isinstance(self.message, Unset):
            message = UNSET
        else:
            message = self.message

        progress: dict[str, Any] | None | Unset
        if isinstance(self.progress, Unset):
            progress = UNSET
        elif isinstance(self.progress, StageSummaryEvent):
            progress = self.progress.to_dict()
        elif isinstance(self.progress, ProgressStartEvent):
            progress = self.progress.to_dict()
        elif isinstance(self.progress, ProgressUpdateEvent):
            progress = self.progress.to_dict()
        elif isinstance(self.progress, ProgressEndEvent):
            progress = self.progress.to_dict()
        elif isinstance(self.progress, TranslationFinishedEvent):
            progress = self.progress.to_dict()
        elif isinstance(self.progress, TranslationErrorEvent):
            progress = self.progress.to_dict()
        else:
            progress = self.progress

        progress_seq = self.progress_seq

        schema_version = self.schema_version

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "created_at": created_at,
                "job_id": job_id,
                "kind": kind,
                "state": state,
                "updated_at": updated_at,
            }
        )
        if error is not UNSET:
            field_dict["error"] = error
        if message is not UNSET:
            field_dict["message"] = message
        if progress is not UNSET:
            field_dict["progress"] = progress
        if progress_seq is not UNSET:
            field_dict["progress_seq"] = progress_seq
        if schema_version is not UNSET:
            field_dict["schema_version"] = schema_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.progress_end_event import ProgressEndEvent
        from ..models.progress_start_event import ProgressStartEvent
        from ..models.progress_update_event import ProgressUpdateEvent
        from ..models.stage_summary_event import StageSummaryEvent
        from ..models.translation_error_event import TranslationErrorEvent
        from ..models.translation_error_payload import TranslationErrorPayload
        from ..models.translation_finished_event import TranslationFinishedEvent

        d = dict(src_dict)
        created_at = isoparse(d.pop("created_at"))

        job_id = d.pop("job_id")

        kind = check_job_status_response_kind(d.pop("kind"))

        state = check_job_status_response_state(d.pop("state"))

        updated_at = isoparse(d.pop("updated_at"))

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

        def _parse_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        message = _parse_message(d.pop("message", UNSET))

        def _parse_progress(
            data: object,
        ) -> (
            None
            | ProgressEndEvent
            | ProgressStartEvent
            | ProgressUpdateEvent
            | StageSummaryEvent
            | TranslationErrorEvent
            | TranslationFinishedEvent
            | Unset
        ):
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                progress_type_0_type_0 = StageSummaryEvent.from_dict(data)

                return progress_type_0_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                progress_type_0_type_1 = ProgressStartEvent.from_dict(data)

                return progress_type_0_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                progress_type_0_type_2 = ProgressUpdateEvent.from_dict(data)

                return progress_type_0_type_2
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                progress_type_0_type_3 = ProgressEndEvent.from_dict(data)

                return progress_type_0_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                progress_type_0_type_4 = TranslationFinishedEvent.from_dict(data)

                return progress_type_0_type_4
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                progress_type_0_type_5 = TranslationErrorEvent.from_dict(data)

                return progress_type_0_type_5
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                None
                | ProgressEndEvent
                | ProgressStartEvent
                | ProgressUpdateEvent
                | StageSummaryEvent
                | TranslationErrorEvent
                | TranslationFinishedEvent
                | Unset,
                data,
            )

        progress = _parse_progress(d.pop("progress", UNSET))

        progress_seq = d.pop("progress_seq", UNSET)

        schema_version = d.pop("schema_version", UNSET)

        job_status_response = cls(
            created_at=created_at,
            job_id=job_id,
            kind=kind,
            state=state,
            updated_at=updated_at,
            error=error,
            message=message,
            progress=progress,
            progress_seq=progress_seq,
            schema_version=schema_version,
        )

        return job_status_response
