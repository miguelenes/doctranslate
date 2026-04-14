from typing import Literal, cast

TranslatorConfigValidateSpecMode = Literal["local", "router"]

TRANSLATOR_CONFIG_VALIDATE_SPEC_MODE_VALUES: set[TranslatorConfigValidateSpecMode] = {
    "local",
    "router",
}


def check_translator_config_validate_spec_mode(value: str) -> TranslatorConfigValidateSpecMode:
    if value in TRANSLATOR_CONFIG_VALIDATE_SPEC_MODE_VALUES:
        return cast(TranslatorConfigValidateSpecMode, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TRANSLATOR_CONFIG_VALIDATE_SPEC_MODE_VALUES!r}")
