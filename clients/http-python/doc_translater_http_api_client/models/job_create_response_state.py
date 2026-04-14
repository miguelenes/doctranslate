from typing import Literal, cast

JobCreateResponseState = Literal["canceled", "failed", "queued", "running", "succeeded"]

JOB_CREATE_RESPONSE_STATE_VALUES: set[JobCreateResponseState] = {
    "canceled",
    "failed",
    "queued",
    "running",
    "succeeded",
}


def check_job_create_response_state(value: str) -> JobCreateResponseState:
    if value in JOB_CREATE_RESPONSE_STATE_VALUES:
        return cast(JobCreateResponseState, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {JOB_CREATE_RESPONSE_STATE_VALUES!r}")
