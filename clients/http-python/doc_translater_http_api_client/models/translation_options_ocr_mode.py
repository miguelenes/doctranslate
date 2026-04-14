from typing import Literal, cast

TranslationOptionsOcrMode = Literal["auto", "force", "hybrid", "off"]

TRANSLATION_OPTIONS_OCR_MODE_VALUES: set[TranslationOptionsOcrMode] = {
    "auto",
    "force",
    "hybrid",
    "off",
}


def check_translation_options_ocr_mode(value: str) -> TranslationOptionsOcrMode:
    if value in TRANSLATION_OPTIONS_OCR_MODE_VALUES:
        return cast(TranslationOptionsOcrMode, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TRANSLATION_OPTIONS_OCR_MODE_VALUES!r}")
