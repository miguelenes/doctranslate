from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.job_create_response_kind import JobCreateResponseKind, check_job_create_response_kind
from ..models.job_create_response_state import JobCreateResponseState, check_job_create_response_state

T = TypeVar("T", bound="JobCreateResponse")


@_attrs_define
class JobCreateResponse:
    """
    Attributes:
        job_id (str):
        kind (JobCreateResponseKind):
        state (JobCreateResponseState):
        status_url (str):
    """

    job_id: str
    kind: JobCreateResponseKind
    state: JobCreateResponseState
    status_url: str

    def to_dict(self) -> dict[str, Any]:
        job_id = self.job_id

        kind: str = self.kind

        state: str = self.state

        status_url = self.status_url

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "job_id": job_id,
                "kind": kind,
                "state": state,
                "status_url": status_url,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        job_id = d.pop("job_id")

        kind = check_job_create_response_kind(d.pop("kind"))

        state = check_job_create_response_state(d.pop("state"))

        status_url = d.pop("status_url")

        job_create_response = cls(
            job_id=job_id,
            kind=kind,
            state=state,
            status_url=status_url,
        )

        return job_create_response
