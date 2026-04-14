from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.health_ready_response_checks import HealthReadyResponseChecks


T = TypeVar("T", bound="HealthReadyResponse")


@_attrs_define
class HealthReadyResponse:
    """
    Attributes:
        ready (bool):
        checks (HealthReadyResponseChecks | Unset):
        message (None | str | Unset):
    """

    ready: bool
    checks: HealthReadyResponseChecks | Unset = UNSET
    message: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        ready = self.ready

        checks: dict[str, Any] | Unset = UNSET
        if not isinstance(self.checks, Unset):
            checks = self.checks.to_dict()

        message: None | str | Unset
        if isinstance(self.message, Unset):
            message = UNSET
        else:
            message = self.message

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "ready": ready,
            }
        )
        if checks is not UNSET:
            field_dict["checks"] = checks
        if message is not UNSET:
            field_dict["message"] = message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.health_ready_response_checks import HealthReadyResponseChecks

        d = dict(src_dict)
        ready = d.pop("ready")

        _checks = d.pop("checks", UNSET)
        checks: HealthReadyResponseChecks | Unset
        if isinstance(_checks, Unset):
            checks = UNSET
        else:
            checks = HealthReadyResponseChecks.from_dict(_checks)

        def _parse_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        message = _parse_message(d.pop("message", UNSET))

        health_ready_response = cls(
            ready=ready,
            checks=checks,
            message=message,
        )

        return health_ready_response
