from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.progress_end_event import ProgressEndEvent
    from ..models.progress_start_event import ProgressStartEvent
    from ..models.progress_update_event import ProgressUpdateEvent
    from ..models.stage_summary_event import StageSummaryEvent
    from ..models.translation_error_event import TranslationErrorEvent
    from ..models.translation_finished_event import TranslationFinishedEvent


T = TypeVar("T", bound="JobEventItem")


@_attrs_define
class JobEventItem:
    """
    Attributes:
        event (ProgressEndEvent | ProgressStartEvent | ProgressUpdateEvent | StageSummaryEvent | TranslationErrorEvent |
            TranslationFinishedEvent):
        seq (int):
    """

    event: (
        ProgressEndEvent
        | ProgressStartEvent
        | ProgressUpdateEvent
        | StageSummaryEvent
        | TranslationErrorEvent
        | TranslationFinishedEvent
    )
    seq: int

    def to_dict(self) -> dict[str, Any]:
        from ..models.progress_end_event import ProgressEndEvent
        from ..models.progress_start_event import ProgressStartEvent
        from ..models.progress_update_event import ProgressUpdateEvent
        from ..models.stage_summary_event import StageSummaryEvent
        from ..models.translation_finished_event import TranslationFinishedEvent

        event: dict[str, Any]
        if isinstance(self.event, StageSummaryEvent):
            event = self.event.to_dict()
        elif isinstance(self.event, ProgressStartEvent):
            event = self.event.to_dict()
        elif isinstance(self.event, ProgressUpdateEvent):
            event = self.event.to_dict()
        elif isinstance(self.event, ProgressEndEvent):
            event = self.event.to_dict()
        elif isinstance(self.event, TranslationFinishedEvent):
            event = self.event.to_dict()
        else:
            event = self.event.to_dict()

        seq = self.seq

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "event": event,
                "seq": seq,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.progress_end_event import ProgressEndEvent
        from ..models.progress_start_event import ProgressStartEvent
        from ..models.progress_update_event import ProgressUpdateEvent
        from ..models.stage_summary_event import StageSummaryEvent
        from ..models.translation_error_event import TranslationErrorEvent
        from ..models.translation_finished_event import TranslationFinishedEvent

        d = dict(src_dict)

        def _parse_event(
            data: object,
        ) -> (
            ProgressEndEvent
            | ProgressStartEvent
            | ProgressUpdateEvent
            | StageSummaryEvent
            | TranslationErrorEvent
            | TranslationFinishedEvent
        ):
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                event_type_0 = StageSummaryEvent.from_dict(data)

                return event_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                event_type_1 = ProgressStartEvent.from_dict(data)

                return event_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                event_type_2 = ProgressUpdateEvent.from_dict(data)

                return event_type_2
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                event_type_3 = ProgressEndEvent.from_dict(data)

                return event_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                event_type_4 = TranslationFinishedEvent.from_dict(data)

                return event_type_4
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            if not isinstance(data, dict):
                raise TypeError()
            event_type_5 = TranslationErrorEvent.from_dict(data)

            return event_type_5

        event = _parse_event(d.pop("event"))

        seq = d.pop("seq")

        job_event_item = cls(
            event=event,
            seq=seq,
        )

        return job_event_item
