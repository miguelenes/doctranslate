from typing import Literal, cast

TranslationMemorySpecTmMode = Literal["exact", "fuzzy", "off", "semantic"]

TRANSLATION_MEMORY_SPEC_TM_MODE_VALUES: set[TranslationMemorySpecTmMode] = {
    "exact",
    "fuzzy",
    "off",
    "semantic",
}


def check_translation_memory_spec_tm_mode(value: str) -> TranslationMemorySpecTmMode:
    if value in TRANSLATION_MEMORY_SPEC_TM_MODE_VALUES:
        return cast(TranslationMemorySpecTmMode, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TRANSLATION_MEMORY_SPEC_TM_MODE_VALUES!r}")
