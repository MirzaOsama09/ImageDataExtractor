"""Extracts structured information (emails, phone numbers, dates, amounts, URLs)
from raw OCR text using regular expressions."""
import re
from typing import Any, Dict, List

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s.\-]?)?(?:\(\d{2,4}\)[\s.\-]?)?\d{3,4}[\s.\-]?\d{3,4}(?:[\s.\-]?\d{2,4})?"
)
URL_RE = re.compile(r"(?:https?://|www\.)[^\s,;]+", re.IGNORECASE)
DATE_RE = re.compile(
    r"\b(?:\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}|\d{4}[/\-.]\d{1,2}[/\-.]\d{1,2}|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{2,4})\b",
    re.IGNORECASE,
)
AMOUNT_RE = re.compile(
    r"(?:[$€£¥]\s?\d[\d,]*(?:\.\d{1,2})?)|(?:\d[\d,]*(?:\.\d{1,2})?\s?(?:USD|EUR|GBP|INR))",
    re.IGNORECASE,
)
# Simplistic check to avoid classifying long digit runs (e.g. IDs) as phone numbers.
MIN_PHONE_DIGITS = 7
MAX_PHONE_DIGITS = 15


def _dedupe(values: List[str]) -> List[str]:
    seen = set()
    result = []
    for v in values:
        cleaned = v.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def _valid_phone(candidate: str) -> bool:
    digits = re.sub(r"\D", "", candidate)
    if not (MIN_PHONE_DIGITS <= len(digits) <= MAX_PHONE_DIGITS):
        return False
    # Require a separator or leading '+' so bare numeric IDs (roll no., etc.) aren't misread as phones.
    return candidate.startswith("+") or bool(re.search(r"[\s.\-()]", candidate))


def _parse_amount(amount: str) -> float:
    return float(re.sub(r"[^\d.]", "", amount) or 0)


def extract_entities(text: str) -> Dict[str, Any]:
    """Return only the important entities actually found in the text (empty
    categories are omitted, and no raw line/text dump is included)."""
    emails = _dedupe(EMAIL_RE.findall(text))
    urls = _dedupe(URL_RE.findall(text))
    dates = _dedupe(DATE_RE.findall(text))
    amounts = _dedupe(AMOUNT_RE.findall(text))
    phones = _dedupe([p for p in PHONE_RE.findall(text) if _valid_phone(p)])

    entities: Dict[str, Any] = {}
    if emails:
        entities["emails"] = emails
    if phones:
        entities["phone_numbers"] = phones
    if urls:
        entities["urls"] = urls
    if dates:
        entities["dates"] = dates
    if amounts:
        entities["amounts"] = amounts
        # Highest amount is typically the total on receipts/invoices.
        entities["likely_total_amount"] = max(amounts, key=_parse_amount)

    return entities
