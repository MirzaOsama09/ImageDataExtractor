"""FastAPI application: upload an image, OCR it, and return extracted data as JSON."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # must run before the ocr modules read env vars at import time

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import app.openai_ocr as openai_ocr
import app.remote_ocr as remote_ocr
from app.document_fields import extract_document_fields
from app.entity_extraction import extract_entities
from app.ocr_errors import OCRError

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR.parent / "static"

ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp", "image/bmp", "image/tiff"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_OCR_PROVIDER = os.environ.get("OCR_PROVIDER", "remote")
OCR_PROVIDERS = {"remote", "openai"}

app = FastAPI(title="Image Data Extractor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/extract")
async def extract(
    file: UploadFile = File(...),
    include_raw_text: bool = False,
    provider: str = DEFAULT_OCR_PROVIDER,
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported content type '{file.content_type}'. "
            f"Allowed types: {sorted(ALLOWED_CONTENT_TYPES)}",
        )

    if provider not in OCR_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported OCR provider '{provider}'. Allowed values: {sorted(OCR_PROVIDERS)}",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 10 MB size limit.")

    try:
        if provider == "openai":
            raw_text, ocr_response = await openai_ocr.extract_text_from_image(
                file_bytes, content_type=file.content_type
            )
        else:
            raw_text, ocr_response = await remote_ocr.extract_text_from_image(file_bytes)
    except OCRError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if provider == "openai":
        # The OpenAI provider already asks the model to return the target fields as
        # JSON directly, so use that instead of running the regex-based extractors.
        document_fields = openai_ocr.parse_document_fields(raw_text)
        entities = {}
        if document_fields is None:
            document_fields = extract_document_fields(raw_text)
            entities = extract_entities(raw_text)
    else:
        document_fields = extract_document_fields(raw_text)
        entities = extract_entities(raw_text)

    # ocr_result comes first so clients can show the raw OCR output before the final parsed data.
    response = {
        "filename": file.filename,
        "provider": provider,
        "ocr_result": ocr_response,
        "final_output": {"document_fields": document_fields, "entities": entities},
    }
    if include_raw_text:
        response["raw_text"] = raw_text
    return response
