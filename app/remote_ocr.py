"""OCR client that delegates recognition to a remote LightOnOCR-2 model served via Ollama."""
import base64
import os
from typing import Any, Dict, Tuple

import httpx

from app.ocr_errors import OCRError

OCR_ENDPOINT = os.environ.get("OCR_ENDPOINT", "http://103.4.95.76:11434")
OCR_MODEL = os.environ.get("OCR_MODEL", "maternion/LightOnOCR-2")
OCR_TIMEOUT_SECONDS = float(os.environ.get("OCR_TIMEOUT_SECONDS", "180"))

_PROMPT = (
    "Transcribe all visible text in this image exactly as it appears, "
    "preserving line breaks. Do not summarize, translate, or add commentary."
)


async def extract_text_from_image(file_bytes: bytes, lang: str = "eng") -> Tuple[str, Dict[str, Any]]:
    """Send image bytes to the remote Ollama-hosted OCR model.

    Returns a tuple of (recognized_text, raw_ocr_response) so callers can
    surface the OCR service's own JSON response alongside the parsed text.
    """
    encoded_image = base64.b64encode(file_bytes).decode("ascii")

    payload = {
        "model": OCR_MODEL,
        "prompt": _PROMPT,
        "images": [encoded_image],
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=OCR_TIMEOUT_SECONDS) as client:
            resp = await client.post(f"{OCR_ENDPOINT}/api/generate", json=payload)
    except httpx.RequestError as exc:
        raise OCRError(f"Could not reach OCR service at {OCR_ENDPOINT}: {exc}") from exc

    if resp.status_code != 200:
        raise OCRError(f"OCR service returned HTTP {resp.status_code}: {resp.text[:500]}")

    try:
        data = resp.json()
    except ValueError as exc:
        raise OCRError("OCR service returned a non-JSON response.") from exc

    text = data.get("response")
    if not text:
        raise OCRError("OCR service returned no recognized text.")

    return text.strip(), data

