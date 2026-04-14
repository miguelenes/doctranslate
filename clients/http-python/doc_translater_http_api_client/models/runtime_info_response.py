from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="RuntimeInfoResponse")


@_attrs_define
class RuntimeInfoResponse:
    """
    Attributes:
        cache_dir (str):
        package_version (str):
        python_version (str):
        app (Literal['doctranslate-http-api'] | Unset):  Default: 'doctranslate-http-api'.
        progress_event_version (str | Unset):  Default: '1'.
        public_schema_version (str | Unset):  Default: '1'.
    """

    cache_dir: str
    package_version: str
    python_version: str
    app: Literal["doctranslate-http-api"] | Unset = "doctranslate-http-api"
    progress_event_version: str | Unset = "1"
    public_schema_version: str | Unset = "1"

    def to_dict(self) -> dict[str, Any]:
        cache_dir = self.cache_dir

        package_version = self.package_version

        python_version = self.python_version

        app = self.app

        progress_event_version = self.progress_event_version

        public_schema_version = self.public_schema_version

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "cache_dir": cache_dir,
                "package_version": package_version,
                "python_version": python_version,
            }
        )
        if app is not UNSET:
            field_dict["app"] = app
        if progress_event_version is not UNSET:
            field_dict["progress_event_version"] = progress_event_version
        if public_schema_version is not UNSET:
            field_dict["public_schema_version"] = public_schema_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cache_dir = d.pop("cache_dir")

        package_version = d.pop("package_version")

        python_version = d.pop("python_version")

        app = cast(Literal["doctranslate-http-api"] | Unset, d.pop("app", UNSET))
        if app != "doctranslate-http-api" and not isinstance(app, Unset):
            raise ValueError(f"app must match const 'doctranslate-http-api', got '{app}'")

        progress_event_version = d.pop("progress_event_version", UNSET)

        public_schema_version = d.pop("public_schema_version", UNSET)

        runtime_info_response = cls(
            cache_dir=cache_dir,
            package_version=package_version,
            python_version=python_version,
            app=app,
            progress_event_version=progress_event_version,
            public_schema_version=public_schema_version,
        )

        return runtime_info_response
