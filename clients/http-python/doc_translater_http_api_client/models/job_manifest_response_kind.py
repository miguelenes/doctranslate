from typing import Literal, cast

JobManifestResponseKind = Literal["translation", "warmup"]

JOB_MANIFEST_RESPONSE_KIND_VALUES: set[JobManifestResponseKind] = {
    "translation",
    "warmup",
}


def check_job_manifest_response_kind(value: str) -> JobManifestResponseKind:
    if value in JOB_MANIFEST_RESPONSE_KIND_VALUES:
        return cast(JobManifestResponseKind, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {JOB_MANIFEST_RESPONSE_KIND_VALUES!r}")
