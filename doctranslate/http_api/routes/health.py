"""Liveness, readiness, and runtime metadata."""

from __future__ import annotations

import sys

from fastapi import APIRouter

from doctranslate import __version__ as package_version
from doctranslate.const import CACHE_FOLDER
from doctranslate.http_api.deps import JobManagerDep
from doctranslate.http_api.deps import SettingsDep
from doctranslate.http_api.models import AssetFileStatus
from doctranslate.http_api.models import AssetStatusResponse
from doctranslate.http_api.models import HealthLiveResponse
from doctranslate.http_api.models import HealthReadyResponse
from doctranslate.http_api.models import RuntimeInfoResponse

router = APIRouter(tags=["health"])


@router.get("/v1/health/live", response_model=HealthLiveResponse)
def health_live() -> HealthLiveResponse:
    return HealthLiveResponse()


@router.get("/v1/health/ready", response_model=HealthReadyResponse)
def health_ready(
    settings: SettingsDep,
    job_manager: JobManagerDep,
) -> HealthReadyResponse:
    checks: dict[str, bool] = {}
    messages: list[str] = []

    try:
        settings.data_root.mkdir(parents=True, exist_ok=True)
        probe = settings.data_root / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        checks["data_root_writable"] = True
    except OSError:
        checks["data_root_writable"] = False
        messages.append(f"data_root not writable: {settings.data_root}")

    try:
        tr = settings.resolved_tmp_root()
        tr.mkdir(parents=True, exist_ok=True)
        probe = tr / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        checks["tmp_root_writable"] = True
    except OSError:
        checks["tmp_root_writable"] = False
        messages.append("tmp_root not writable")

    assets_ready = True
    if settings.require_assets_ready:
        try:
            from doctranslate.assets import assets as assets_mod

            file_list = assets_mod.generate_all_assets_file_list()
            for category, descs in file_list.items():
                for desc in descs:
                    name = desc["name"]
                    sha = desc["sha3_256"]
                    p = assets_mod.get_cache_file_path(name, category)
                    if not assets_mod.verify_file(p, sha):
                        assets_ready = False
                        break
                if not assets_ready:
                    break
        except Exception:
            assets_ready = False
        checks["assets_ready"] = assets_ready
        if not assets_ready:
            messages.append("required assets missing or corrupt")
    else:
        checks["assets_ready"] = True

    checks["accepting_jobs"] = job_manager.accepts_new_jobs()
    if not checks["accepting_jobs"]:
        messages.append("job queue at capacity")

    ready = all(checks.values())
    return HealthReadyResponse(
        ready=ready,
        checks=checks,
        message="; ".join(messages) if messages else None,
    )


@router.get("/v1/runtime", response_model=RuntimeInfoResponse)
def runtime_info() -> RuntimeInfoResponse:
    return RuntimeInfoResponse(
        package_version=package_version,
        python_version=sys.version.split()[0],
        cache_dir=str(CACHE_FOLDER),
    )


@router.get("/v1/assets/status", response_model=AssetStatusResponse)
def assets_status() -> AssetStatusResponse:
    from doctranslate.assets import assets as assets_mod

    files: list = []
    all_ok = True
    file_list = assets_mod.generate_all_assets_file_list()
    for category, descs in file_list.items():
        for desc in descs:
            name = desc["name"]
            sha = desc["sha3_256"]
            p = assets_mod.get_cache_file_path(name, category)
            ok = assets_mod.verify_file(p, sha)
            if not ok:
                all_ok = False
            files.append(
                AssetFileStatus(category=category, name=name, present=ok),
            )
    return AssetStatusResponse(ready=all_ok, files=files)
