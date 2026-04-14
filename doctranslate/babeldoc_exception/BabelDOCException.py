"""Re-export exceptions from ``doctranslate.doctranslate_exception``."""

from doctranslate.doctranslate_exception.BabelDOCException import ContentFilterError
from doctranslate.doctranslate_exception.BabelDOCException import ExtractTextError
from doctranslate.doctranslate_exception.BabelDOCException import (
    InputFileGeneratedByBabelDOCError,
)
from doctranslate.doctranslate_exception.BabelDOCException import ScannedPDFError

__all__ = [
    "ContentFilterError",
    "ExtractTextError",
    "InputFileGeneratedByBabelDOCError",
    "ScannedPDFError",
]
