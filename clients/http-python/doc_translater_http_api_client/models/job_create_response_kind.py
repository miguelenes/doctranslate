from typing import Literal, cast

JobCreateResponseKind = Literal["translation", "warmup"]

JOB_CREATE_RESPONSE_KIND_VALUES: set[JobCreateResponseKind] = {
    "translation",
    "warmup",
}


def check_job_create_response_kind(value: str) -> JobCreateResponseKind:
    if value in JOB_CREATE_RESPONSE_KIND_VALUES:
        return cast(JobCreateResponseKind, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {JOB_CREATE_RESPONSE_KIND_VALUES!r}")
