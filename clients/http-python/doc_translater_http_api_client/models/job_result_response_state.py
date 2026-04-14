from typing import Literal, cast

JobResultResponseState = Literal["canceled", "failed", "queued", "running", "succeeded"]

JOB_RESULT_RESPONSE_STATE_VALUES: set[JobResultResponseState] = {
    "canceled",
    "failed",
    "queued",
    "running",
    "succeeded",
}


def check_job_result_response_state(value: str) -> JobResultResponseState:
    if value in JOB_RESULT_RESPONSE_STATE_VALUES:
        return cast(JobResultResponseState, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {JOB_RESULT_RESPONSE_STATE_VALUES!r}")
