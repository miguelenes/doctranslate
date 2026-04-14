from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="WebhookCreateSpec")


@_attrs_define
class WebhookCreateSpec:
    """Terminal webhook configuration (JSON body on ``POST /v1/jobs/json``).

    Attributes:
        url (str):
        secret (None | str | Unset):
        secret_env (None | str | Unset):
    """

    url: str
    secret: None | str | Unset = UNSET
    secret_env: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        url = self.url

        secret: None | str | Unset
        if isinstance(self.secret, Unset):
            secret = UNSET
        else:
            secret = self.secret

        secret_env: None | str | Unset
        if isinstance(self.secret_env, Unset):
            secret_env = UNSET
        else:
            secret_env = self.secret_env

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "url": url,
            }
        )
        if secret is not UNSET:
            field_dict["secret"] = secret
        if secret_env is not UNSET:
            field_dict["secret_env"] = secret_env

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        url = d.pop("url")

        def _parse_secret(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        secret = _parse_secret(d.pop("secret", UNSET))

        def _parse_secret_env(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        secret_env = _parse_secret_env(d.pop("secret_env", UNSET))

        webhook_create_spec = cls(
            url=url,
            secret=secret,
            secret_env=secret_env,
        )

        return webhook_create_spec
