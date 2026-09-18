"""Extracts common labeled fields (name, roll no., marks, etc.) from documents
such as academic result cards / marksheets, based on OCR text that may be
plain label:value lines OR natural-language/markdown formatted (headings,
bold text, sentences like "Certified that NAME", HTML mark tables, etc.)."""
import re
from typing import Dict, List, Optional, Tuple

_BOLD_RE = re.compile(r"\*\*(.*?)\*\*")
_ITALIC_RE = re.compile(r"(?<!\w)\*(.*?)\*(?!\w)")
_HEADING_RE = re.compile(r"^#+\s*")
_LATEX_RE = re.compile(r"\$[^$]*\$")
_RULE_RE = re.compile(r"^[-=*_]{3,}$")

_TITLE_KEYWORDS_RE = re.compile(
    r"\b(board|university|school|college|examination|exam|marksheet|mark\s*sheet|"
    r"result|certificate|statement\s*of\s*marks)\b",
    re.IGNORECASE,
)

# Each field maps to an ordered list of full-line regex patterns (checked in order,
# first line + first pattern to match wins). Patterns handle both "Label: value"
# forms and natural-language/sentence forms produced by vision-language OCR models.
_FIELD_PATTERNS: List[Tuple[str, List[re.Pattern]]] = [
    (
        "date_of_birth",
        [
            re.compile(r"date\s*of\s*birth\s*(?:is)?\s*[:\-]?\s*(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})", re.IGNORECASE),
            re.compile(r"\bd\.?\s*o\.?\s*b\.?\s*[:\-]?\s*(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})", re.IGNORECASE),
        ],
    ),
    (
        "father_name",
        [
            re.compile(r"father'?s?\s*name\s*[:\-]?\s*(.+)", re.IGNORECASE),
            re.compile(r"son\s*/?\s*daughter\s+of\s+(.+?)\s*(?:\(|$)", re.IGNORECASE),
            re.compile(r"\bs\s*/\s*o\b\s*[:\-]?\s*(.+)", re.IGNORECASE),
            re.compile(r"\bd\s*/\s*o\b\s*[:\-]?\s*(.+)", re.IGNORECASE),
        ],
    ),
    (
        "mother_name",
        [re.compile(r"mother'?s?\s*name\s*[:\-]?\s*(.+)", re.IGNORECASE)],
    ),
    (
        "registration_number",
        [
            re.compile(r"regist(?:ration)?\.?\s*(?:no|number|id)\.?\s*[:\-]?\s*(.+)", re.IGNORECASE),
            re.compile(r"enrol?lment\s*(?:no|number)\.?\s*[:\-]?\s*(.+)", re.IGNORECASE),
        ],
    ),
    (
        "roll_number",
        [re.compile(r"roll\s*(?:no|number)\.?\s*[:\-]?\s*(.+)", re.IGNORECASE)],
    ),
    (
        "name",
        [
            re.compile(r"candidate'?s?\s*name\s*[:\-]?\s*(.+)", re.IGNORECASE),
            re.compile(r"student'?s?\s*name\s*[:\-]?\s*(.+)", re.IGNORECASE),
            re.compile(r"certified\s+that\s+(.+?)\s*$", re.IGNORECASE),
            re.compile(r"^name\s*[:\-]?\s*(.+)", re.IGNORECASE),
        ],
    ),
    (
        "date",
        [
            re.compile(r"date\s*of\s*issue\s*[:\-]?\s*(.+)", re.IGNORECASE),
            re.compile(r"\bdated\s+(.+)", re.IGNORECASE),
            re.compile(r"^date\s*[:\-]?\s*(.+)$", re.IGNORECASE),
        ],
    ),
]

_MARKS_PAIR_RE = re.compile(r"\b(\d{1,4})\s*/\s*(\d{1,4})\b")
_TABLE_TOTAL_RE = re.compile(
    r"<tr>\s*<td[^>]*>\s*</td>\s*<td[^>]*>\s*(?:grand\s+)?total\s*</td>\s*"
    r"<td[^>]*>\s*(\d+)\s*</td>\s*<td[^>]*>\s*(\d+)\s*</td>\s*</tr>",
    re.IGNORECASE | re.DOTALL,
)
_THEAD_RE = re.compile(r"<thead>(.*?)</thead>", re.IGNORECASE | re.DOTALL)


def _normalize_line(line: str) -> str:
    """Strip markdown decoration (headings, bold/italic, LaTeX) from a line."""
    line = _LATEX_RE.sub("", line)
    line = _HEADING_RE.sub("", line)
    line = _BOLD_RE.sub(r"\1", line)
    line = _ITALIC_RE.sub(r"\1", line)
    return line.strip()


def _clean_value(value: str) -> str:
    value = re.sub(r"\(.*?\)\s*$", "", value)  # trailing parenthetical, e.g. "(Eighteenth April...)"
    return re.sub(r"^[\s:\-.]+|[\s:\-.,]+$", "", value).strip()


def _extract_title(lines: List[str]) -> Optional[str]:
    for line in lines[:8]:
        if _TITLE_KEYWORDS_RE.search(line) and len(line) > 4:
            return line.strip()
    return lines[0].strip() if lines else None


def _extract_marks(raw_text: str, lines: List[str]) -> Dict[str, str]:
    marks: Dict[str, str] = {}

    table_match = _TABLE_TOTAL_RE.search(raw_text)
    if table_match:
        obtained_first = False
        head_match = _THEAD_RE.search(raw_text)
        if head_match:
            head = head_match.group(1).lower()
            max_pos, obt_pos = head.find("maximum"), head.find("obtained")
            if max_pos != -1 and obt_pos != -1:
                obtained_first = obt_pos < max_pos
        g1, g2 = table_match.group(1), table_match.group(2)
        marks["total_marks"], marks["candidate_marks"] = (g2, g1) if obtained_first else (g1, g2)
        return marks

    # Fallback: plain "TOTAL 1100 984" style line without HTML markup.
    for line in lines:
        if re.search(r"total", line, re.IGNORECASE):
            numbers = re.findall(r"\d{2,4}", line)
            if len(numbers) >= 2:
                marks["total_marks"], marks["candidate_marks"] = numbers[0], numbers[1]
                return marks

    # Last resort: an explicit "NNN/NNN" style mark pair.
    for line in lines:
        if re.search(r"marks?|total", line, re.IGNORECASE):
            pair = _MARKS_PAIR_RE.search(line)
            if pair:
                marks["candidate_marks"], marks["total_marks"] = pair.group(1), pair.group(2)
                return marks

    return marks


def extract_document_fields(text: str) -> Dict[str, str]:
    """Scan OCR'd text for common labeled document fields (name, father's name,
    roll/registration numbers, dates, marks, title), handling both simple
    "Label: value" layouts and natural-language/markdown OCR output."""
    raw_lines = [line for line in text.splitlines() if line.strip() and not _RULE_RE.match(line.strip())]
    lines = [_normalize_line(line) for line in raw_lines]
    lines = [line for line in lines if line]

    fields: Dict[str, str] = {}
    for key, patterns in _FIELD_PATTERNS:
        for line in lines:
            if key in fields:
                break
            for pattern in patterns:
                match = pattern.search(line)
                if match:
                    value = _clean_value(match.group(1))
                    if value:
                        fields[key] = value
                    break

    fields.update({k: v for k, v in _extract_marks(text, lines).items() if k not in fields})

    title = _extract_title(lines)
    if title:
        fields["title"] = title

    return fields
