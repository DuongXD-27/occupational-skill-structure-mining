"""
src/cleaner/title.py
QR-04: Normalize raw_job_title → normalized_job_title

Rules (from docs/data_cleaning/data_quality_rules.md §5):
- Surface cleaning ONLY. Never merge distinct roles.
- raw_job_title is immutable.
- Steps: trim → collapse spaces → strip meaningless specials → Title Case
  → expand abbreviations → strip non-title noise (salary, bonus, punctuation).
- Flag AMBIGUOUS_TITLE if two distinct roles in one title.
- Flag TITLE_TOO_SHORT (<3 chars after cleaning).
- Flag TITLE_TOO_LONG (>100 chars; truncate).
"""

from __future__ import annotations

import re
from typing import Optional


# ---------------------------------------------------------------------------
# Abbreviation expansions (format-only, no semantic change)
# ---------------------------------------------------------------------------

_ABBREVS = {
    r"\bSr\.?\b": "Senior",
    r"\bJr\.?\b": "Junior",
    r"\bMgr\.?\b": "Manager",
    r"\bEng\.?\b": "Engineer",
    r"\bDev\.?\b": "Developer",
    r"\bDir\.?\b": "Director",
    r"\bAssoc\.?\b": "Associate",
}

_ABBREV_COMPILED = [(re.compile(pat, re.IGNORECASE), repl) for pat, repl in _ABBREVS.items()]

# ---------------------------------------------------------------------------
# Noise patterns to strip (salary, bonus, trailing punctuation)
# ---------------------------------------------------------------------------

# Salary: "Up to 75M", "upto 1500 USD", "$2000", "2000$", "lên đến 50tr"
_SALARY_RE = re.compile(
    r"(\b(up\s*to|upto|lên\s*đến|tới|to)\s*\d[\d,.]*\s*(M|K|USD|VND|tr|triệu)?|"
    r"\$\s*\d[\d,.]*|\d[\d,.]*\s*\$)",
    re.IGNORECASE,
)

# Bonus/perk phrases
_BONUS_RE = re.compile(
    r"\s*[-–]\s*(bonus|thưởng|package|allowance|incentive)\b.*$",
    re.IGNORECASE,
)

# "English required" type trailing suffix after comma or dash
_TRAILING_SUFFIX_RE = re.compile(
    r"\s*[,\-–|]\s*(english\s+required|yêu\s+cầu\s+tiếng\s+anh|fluent\s+english).*$",
    re.IGNORECASE,
)

# Trailing dangling punctuation: / , - | at end of string
_TRAILING_PUNCT_RE = re.compile(r"[\s/,\-–|]+$")

# Leading list numbers/bullets: "1. ", "- ", "* "
_LEADING_NOISE_RE = re.compile(r"^[\d]+\.\s*|^[-*#•]\s*")

# Parentheses and square brackets (but keep content for technical tokens like C++)
_PAREN_RE = re.compile(r"[(){}\[\]]")

# ---------------------------------------------------------------------------
# Dual-role detection
# ---------------------------------------------------------------------------

# Dual role: two different occupational tokens separated by / or |
# Allow prefix words (e.g. "Data Engineer / Data Analyst")
_DUAL_ROLE_RE = re.compile(
    r"(?:\w+\s+)*(?:analyst|engineer|scientist|developer|architect|manager|designer|"
    r"consultant|specialist|researcher)\s*[/|]\s*"
    r"(?:\w+\s+)*(?:analyst|engineer|scientist|developer|architect|manager|designer|"
    r"consultant|specialist|researcher)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Title Case helper (smarter than str.title() which uppercases after apostrophe)
# ---------------------------------------------------------------------------

_SMALL_WORDS = {"a", "an", "the", "and", "or", "but", "for", "nor",
                "on", "at", "to", "by", "of", "in", "with"}

# Tokens to keep in UPPER (well-known acronyms)
_KEEP_UPPER = {"ai", "ml", "nlp", "llm", "bi", "ux", "ui", "api",
               "sql", "etl", "elt", "qa", "ba", "hr", "sap", "erp",
               "aws", "gcp", "az", "ci", "cd", "oop"}


def _smart_title_case(text: str) -> str:
    words = text.split()
    result = []
    for i, word in enumerate(words):
        lower_word = word.lower()
        # Preserve tokens with MEANINGFUL internal structure (C++, PyTorch, iOS)
        # but NOT simple ALL-CAPS words like "DATA" or "ANALYST"
        has_meaningful_internal = bool(re.search(r"[+]{2}|(?<=[a-z])[A-Z]|/", word))
        if has_meaningful_internal:
            result.append(word)
        elif lower_word in _KEEP_UPPER:
            result.append(word.upper())
        elif i > 0 and lower_word in _SMALL_WORDS:
            result.append(lower_word)
        else:
            result.append(word.capitalize())
    return " ".join(result)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_title(raw: Optional[str]) -> tuple[Optional[str], list[str]]:
    """
    Normalize raw_job_title.

    Returns
    -------
    (normalized_job_title, quality_flags)
    """
    flags: list[str] = []

    if not raw or not raw.strip():
        return None, ["MISSING_JOB_TITLE"]

    text = raw.strip()

    # Step 1: strip leading list markers
    text = _LEADING_NOISE_RE.sub("", text).strip()

    # Step 2: strip salary mentions
    text = _SALARY_RE.sub("", text).strip()

    # Step 3: strip trailing bonus/perk phrases
    text = _BONUS_RE.sub("", text).strip()

    # Step 4: strip trailing language requirement suffixes
    text = _TRAILING_SUFFIX_RE.sub("", text).strip()

    # Step 5: strip parentheses / square brackets (keep content)
    text = _PAREN_RE.sub("", text).strip()

    # Step 6: collapse multiple spaces
    text = re.sub(r"\s{2,}", " ", text).strip()

    # Step 7: strip trailing dangling punctuation
    text = _TRAILING_PUNCT_RE.sub("", text).strip()

    # Step 8: expand abbreviations
    for pattern, repl in _ABBREV_COMPILED:
        text = pattern.sub(repl, text)

    # Step 9: Title Case
    text = _smart_title_case(text)

    # Step 10: collapse spaces again (abbreviation expansion may add spaces)
    text = re.sub(r"\s{2,}", " ", text).strip()

    # --- Flags ---
    if not text or len(text) < 3:
        return text or None, ["TITLE_TOO_SHORT"]

    if _DUAL_ROLE_RE.search(text):
        flags.append("AMBIGUOUS_TITLE")

    if len(text) > 100:
        text = text[:100].rstrip()
        flags.append("TITLE_TOO_LONG")

    return text, flags
