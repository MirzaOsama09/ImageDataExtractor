# Image Data Extractor

Upload an image, run OCR, and get the extracted text plus structured entities (emails, phone numbers, URLs, dates, amounts) as JSON.

## Prerequisites

- Python 3.9+
- Tesseract OCR engine installed and available on PATH
  - Windows: install from https://github.com/UB-Mannheim/tesseract/wiki
  - macOS: `brew install tesseract`
  - Linux: `sudo apt install tesseract-ocr`

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000 in a browser to use the upload UI, or call the API directly:

```powershell
curl.exe -F "file=@path\to\image.png" http://127.0.0.1:8000/api/extract
```

## Response shape

```json
{
  "filename": "receipt.png",
  "raw_text": "...",
  "entities": {
    "emails": [],
    "phone_numbers": [],
    "urls": [],
    "dates": [],
    "amounts": [],
    "lines": []
  }
}
```
