from typing import Literal, cast

ArtifactKind = Literal[
    "auto_extracted_glossary_csv",
    "dual_plain_pdf",
    "dual_watermarked_pdf",
    "metrics_json",
    "mono_plain_pdf",
    "mono_watermarked_pdf",
]

ARTIFACT_KIND_VALUES: set[ArtifactKind] = {
    "auto_extracted_glossary_csv",
    "dual_plain_pdf",
    "dual_watermarked_pdf",
    "metrics_json",
    "mono_plain_pdf",
    "mono_watermarked_pdf",
}


def check_artifact_kind(value: str) -> ArtifactKind:
    if value in ARTIFACT_KIND_VALUES:
        return cast(ArtifactKind, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {ARTIFACT_KIND_VALUES!r}")
