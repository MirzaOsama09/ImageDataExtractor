"""Shared error type for all OCR provider backends."""


class OCRError(Exception):
    """Raised when an OCR provider cannot process the image."""
