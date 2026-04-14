from typing import Literal, cast

JobManifestResponseState = Literal["canceled", "failed", "queued", "running", "succeeded"]

JOB_MANIFEST_RESPONSE_STATE_VALUES: set[JobManifestResponseState] = {
    "canceled",
    "failed",
    "queued",
    "running",
    "succeeded",
}


def check_job_manifest_response_state(value: str) -> JobManifestResponseState:
    if value in JOB_MANIFEST_RESPONSE_STATE_VALUES:
        return cast(JobManifestResponseState, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {JOB_MANIFEST_RESPONSE_STATE_VALUES!r}")
