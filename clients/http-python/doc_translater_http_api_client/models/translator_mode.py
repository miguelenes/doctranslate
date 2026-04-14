from typing import Literal, cast

TranslatorMode = Literal["local", "openai", "router"]

TRANSLATOR_MODE_VALUES: set[TranslatorMode] = {
    "local",
    "openai",
    "router",
}


def check_translator_mode(value: str) -> TranslatorMode:
    if value in TRANSLATOR_MODE_VALUES:
        return cast(TranslatorMode, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TRANSLATOR_MODE_VALUES!r}")
