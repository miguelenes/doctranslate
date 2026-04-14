"""Public errors for the PDF translation pipeline and translators."""


class ScannedPDFError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class ExtractTextError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class PriorTranslatedInputError(Exception):
    """Raised when a PDF is already marked as produced by this engine."""

    def __init__(self, message: str):
        super().__init__(message)


class ContentFilterError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
