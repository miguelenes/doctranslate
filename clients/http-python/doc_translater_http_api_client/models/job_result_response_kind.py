from typing import Literal, cast

JobResultResponseKind = Literal["translation", "warmup"]

JOB_RESULT_RESPONSE_KIND_VALUES: set[JobResultResponseKind] = {
    "translation",
    "warmup",
}


def check_job_result_response_kind(value: str) -> JobResultResponseKind:
    if value in JOB_RESULT_RESPONSE_KIND_VALUES:
        return cast(JobResultResponseKind, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {JOB_RESULT_RESPONSE_KIND_VALUES!r}")
