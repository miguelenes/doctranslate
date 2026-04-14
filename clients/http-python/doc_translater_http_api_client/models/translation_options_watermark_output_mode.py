from typing import Literal, cast

TranslationOptionsWatermarkOutputMode = Literal["both", "no_watermark", "watermarked"]

TRANSLATION_OPTIONS_WATERMARK_OUTPUT_MODE_VALUES: set[TranslationOptionsWatermarkOutputMode] = {
    "both",
    "no_watermark",
    "watermarked",
}


def check_translation_options_watermark_output_mode(value: str) -> TranslationOptionsWatermarkOutputMode:
    if value in TRANSLATION_OPTIONS_WATERMARK_OUTPUT_MODE_VALUES:
        return cast(TranslationOptionsWatermarkOutputMode, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TRANSLATION_OPTIONS_WATERMARK_OUTPUT_MODE_VALUES!r}")
