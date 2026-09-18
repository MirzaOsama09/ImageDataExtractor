"""OCR client that delegates recognition to an OpenAI vision-capable chat model."""
import base64
import json
import os
from typing import Any, Dict, Optional, Tuple

import httpx

from app.ocr_errors import OCRError

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT_SECONDS = float(os.environ.get("OPENAI_TIMEOUT_SECONDS", "180"))
# "low" fixes image tokens to a small flat cost (cheaper, coarser); "high"/"auto" tile the
# image into more tokens for better detail on small text. This is usually the dominant
# cost driver, far more than the text prompt.
OPENAI_IMAGE_DETAIL = os.environ.get("OPENAI_IMAGE_DETAIL", "auto")

# Keys the model must return. Asking for this exact, compact schema (instead of a full
# transcription) keeps both the prompt and the model's JSON reply short and cheap.
DOCUMENT_FIELDS = [
    "name",
    "cnic",
    "dob",
    "fatherName",
    "fatherCnic",
    "docTitle",
    "docDate",
    "totalMarks",
    "obtainedMarks",
    "rollNumber",
    "registrationNumber",
    "instituteName",
    "boardName",
]

_PROMPT = (
    'Extract these fields from the image and return ONLY valid compact JSON with exactly these keys: '
    'name,cnic,dob,fatherName,fatherCnic,docTitle,docDate,totalMarks,obtainedMarks,rollNumber,'
    'registrationNumber,instituteName,boardName. '
    'Use visible values; use null if absent. Preserve text/numbers as shown. '
    'CNIC is usually beside the name. If totalMarks is not shown, sum all maximum marks.'
)

_CONTENT_TYPE_TO_MIME = {
    "image/png": "image/png",
    "image/jpeg": "image/jpeg",
    "image/webp": "image/webp",
    "image/bmp": "image/bmp",
    "image/tiff": "image/tiff",
}


async def extract_text_from_image(
    file_bytes: bytes, lang: str = "eng", content_type: str = "image/png"
) -> Tuple[str, Dict[str, Any]]:
    """Send image bytes to an OpenAI vision model and ask it to return the target
    document fields directly as JSON (cheaper than a full-page transcription).

    Returns a tuple of (json_text, raw_api_response) so callers can surface
    OpenAI's own JSON response alongside the model's JSON reply text.
    """
    if not OPENAI_API_KEY:
        raise OCRError(
            "OPENAI_API_KEY is not set. Set the OPENAI_API_KEY environment variable "
            "before selecting the 'openai' OCR provider."
        )

    mime_type = _CONTENT_TYPE_TO_MIME.get(content_type, "image/png")
    encoded_image = base64.b64encode(file_bytes).decode("ascii")
    data_url = f"data:{mime_type};base64,{encoded_image}"

    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0,
        "max_tokens": 400,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _PROMPT},
                    {"type": "image_url", "image_url": {"url": data_url, "detail": OPENAI_IMAGE_DETAIL}},
                ],
            }
        ],
    }
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=OPENAI_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                f"{OPENAI_BASE_URL}/chat/completions", json=payload, headers=headers
            )
    except httpx.RequestError as exc:
        raise OCRError(f"Could not reach OpenAI API at {OPENAI_BASE_URL}: {exc}") from exc

    if resp.status_code != 200:
        raise OCRError(f"OpenAI API returned HTTP {resp.status_code}: {resp.text[:500]}")

    try:
        data = resp.json()
    except ValueError as exc:
        raise OCRError("OpenAI API returned a non-JSON response.") from exc

    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OCRError("OpenAI API response did not contain recognized text.") from exc

    if not text:
        raise OCRError("OpenAI API returned no recognized text.")

    return text.strip(), data


def parse_document_fields(json_text: str) -> Optional[Dict[str, Any]]:
    """Parse the model's JSON reply and normalize it to exactly DOCUMENT_FIELDS keys.

    Returns None if the reply isn't valid JSON, so the caller can fall back
    to regex-based extraction on the raw text instead.
    """
    try:
        parsed = json.loads(json_text)
    except ValueError:
        return None
    if not isinstance(parsed, dict):
        return None
    return {key: parsed.get(key) for key in DOCUMENT_FIELDS}

