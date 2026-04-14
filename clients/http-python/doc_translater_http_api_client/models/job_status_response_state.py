from typing import Literal, cast

JobStatusResponseState = Literal["canceled", "failed", "queued", "running", "succeeded"]

JOB_STATUS_RESPONSE_STATE_VALUES: set[JobStatusResponseState] = {
    "canceled",
    "failed",
    "queued",
    "running",
    "succeeded",
}


def check_job_status_response_state(value: str) -> JobStatusResponseState:
    if value in JOB_STATUS_RESPONSE_STATE_VALUES:
        return cast(JobStatusResponseState, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {JOB_STATUS_RESPONSE_STATE_VALUES!r}")
