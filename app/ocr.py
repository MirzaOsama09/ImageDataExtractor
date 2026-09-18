"""OCR helper that converts image bytes into text using Tesseract via pytesseract."""
import io
import os
import shutil

import pytesseract
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_IMAGE_DIMENSION = 4000

# Fall back to the default Windows install location if tesseract isn't on PATH.
_DEFAULT_WINDOWS_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]
if not shutil.which("tesseract"):
    for _path in _DEFAULT_WINDOWS_PATHS:
        if os.path.isfile(_path):
            pytesseract.pytesseract.tesseract_cmd = _path
            break


class OCRError(Exception):
    """Raised when an image cannot be read or processed for OCR."""


MIN_IMAGE_DIMENSION = 1200  # documents with small text OCR much better when upscaled first


def _preprocess(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    image = image.convert("L")  # grayscale improves OCR accuracy
    if max(image.size) > MAX_IMAGE_DIMENSION:
        image.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))
    elif max(image.size) < MIN_IMAGE_DIMENSION:
        scale = MIN_IMAGE_DIMENSION / max(image.size)
        image = image.resize((int(image.width * scale), int(image.height * scale)), Image.LANCZOS)
    image = ImageOps.autocontrast(image)
    # Binarize so faint scan/photo backgrounds don't confuse the recognizer.
    image = image.point(lambda px: 255 if px > 150 else 0)
    return image


def extract_text_from_image(file_bytes: bytes, lang: str = "eng") -> str:
    """Run OCR on raw image bytes and return the recognized text."""
    try:
        image = Image.open(io.BytesIO(file_bytes))
        image.load()
    except UnidentifiedImageError as exc:
        raise OCRError("File is not a valid or supported image.") from exc

    processed = _preprocess(image)

    try:
        # PSM 6: treat the image as a single uniform block of text, well suited to forms/cards.
        text = pytesseract.image_to_string(processed, lang=lang, config="--psm 6")
    except pytesseract.TesseractNotFoundError as exc:
        raise OCRError(
            "Tesseract OCR engine is not installed or not found on PATH. "
            "Install it from https://github.com/UB-Mannheim/tesseract/wiki (Windows) "
            "or via your OS package manager."
        ) from exc

    return text.strip()
