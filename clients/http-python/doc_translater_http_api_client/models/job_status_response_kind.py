from typing import Literal, cast

JobStatusResponseKind = Literal["translation", "warmup"]

JOB_STATUS_RESPONSE_KIND_VALUES: set[JobStatusResponseKind] = {
    "translation",
    "warmup",
}


def check_job_status_response_kind(value: str) -> JobStatusResponseKind:
    if value in JOB_STATUS_RESPONSE_KIND_VALUES:
        return cast(JobStatusResponseKind, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {JOB_STATUS_RESPONSE_KIND_VALUES!r}")
