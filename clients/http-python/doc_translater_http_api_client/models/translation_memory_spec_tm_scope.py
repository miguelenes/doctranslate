from typing import Literal, cast

TranslationMemorySpecTmScope = Literal["document", "global", "project"]

TRANSLATION_MEMORY_SPEC_TM_SCOPE_VALUES: set[TranslationMemorySpecTmScope] = {
    "document",
    "global",
    "project",
}


def check_translation_memory_spec_tm_scope(value: str) -> TranslationMemorySpecTmScope:
    if value in TRANSLATION_MEMORY_SPEC_TM_SCOPE_VALUES:
        return cast(TranslationMemorySpecTmScope, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TRANSLATION_MEMORY_SPEC_TM_SCOPE_VALUES!r}")
