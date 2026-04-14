from typing import Literal, cast

PublicErrorCode = Literal[
    "canceled",
    "input_error",
    "internal_error",
    "not_found",
    "open_failed",
    "translator_error",
    "unsupported_configuration",
    "validation_error",
]

PUBLIC_ERROR_CODE_VALUES: set[PublicErrorCode] = {
    "canceled",
    "input_error",
    "internal_error",
    "not_found",
    "open_failed",
    "translator_error",
    "unsupported_configuration",
    "validation_error",
}


def check_public_error_code(value: str) -> PublicErrorCode:
    if value in PUBLIC_ERROR_CODE_VALUES:
        return cast(PublicErrorCode, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {PUBLIC_ERROR_CODE_VALUES!r}")
