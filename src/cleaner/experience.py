"""
src/cleaner/experience.py
QR-03: Parse raw_experience → experience_min_years / experience_max_years

Rules (from docs/data_cleaning/data_quality_rules.md §4):
- raw_experience is immutable.
- -1 in experience_max_years = explicitly unbounded above (e.g. "2+ years").
- null = indeterminate / parse failure.
- Seniority labels (Senior, Junior, Mid-level) → null/null + EXPERIENCE_LEVEL_ONLY.
- Scraper anomalies (At office, Hybrid, addresses) → null/null + SCRAPER_FIELD_MISMATCH.
- Priority: bounded range (X-Y) → one-sided (X+, <X) → single number.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Mapping of Vietnamese base letters with stroke that NFD cannot decompose
_STROKE_MAP = str.maketrans({
    "\u0111": "d",  # đ → d
    "\u0110": "D",  # Đ → D
    "\u01b0": "u",  # ư → u
    "\u01af": "U",  # Ư → U
    "\u01a1": "o",  # ơ → o
    "\u01a0": "O",  # Ơ → O
})


def _strip_accents(text: str) -> str:
    """Remove Vietnamese and other accents for regex matching."""
    text = text.translate(_STROKE_MAP)          # handle stroke letters first
    nfkd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def _normalize(text: str) -> str:
    return _strip_accents(text.lower().strip())



# ---------------------------------------------------------------------------
# Scraper anomaly detection (At office / Hybrid / address strings)
# ---------------------------------------------------------------------------

_WORK_MODE_RE = re.compile(
    r"^\s*(at\s+office|hybrid|remote)\b",
    re.IGNORECASE,
)

# If the string looks like a street address (has digits + street-like words)
_ADDRESS_RE = re.compile(
    r"\b(street|road|floor|tower|plaza|district|nguyen|le\s|tran\s|thai\s|ton\s)",
    re.IGNORECASE,
)


def _is_scraper_anomaly(raw: str) -> bool:
    text = raw.strip()
    if _WORK_MODE_RE.match(text):
        return True
    if _ADDRESS_RE.search(text):
        return True
    return False


# ---------------------------------------------------------------------------
# Seniority-level-only detection
# ---------------------------------------------------------------------------

_SENIORITY_RE = re.compile(
    r"^\s*(senior|junior|mid[\s\-]?level|fresher|entry[\s\-]?level|lead|principal|staff)\s*$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Parsing patterns (priority order)
# ---------------------------------------------------------------------------

# "X - Y years" / "X đến Y năm" / "từ X đến Y"
_RANGE_RE = re.compile(
    r"(?:tu\s+)?(\d+(?:\.\d+)?)\s*(?:den|[-~]|to)\s*(\d+(?:\.\d+)?)"
    r"\s*(?:nam|years?|yr)?|"
    r"tu\s+(\d+(?:\.\d+)?)\s+den\s+(\d+(?:\.\d+)?)\s*(?:nam|years?|yr)?",
    re.IGNORECASE,
)

# "Trên X" / "over X" / "X+" / ">X" / "≥X" / "at least X"
_LOWER_BOUND_RE = re.compile(
    r"(?:tren|over|at\s+least|more\s+than|minimum|min\.?|≥|>=)\s*(\d+(?:\.\d+)?)"
    r"\s*(?:nam|years?|yr)?|(\d+(?:\.\d+)?)\s*\+\s*(?:nam|years?|yr)?|"
    r"[>≥]\s*(\d+(?:\.\d+)?)\s*(?:nam|years?|yr)?",
    re.IGNORECASE,
)

# "Dưới X" / "under X" / "<X" / "≤X" / "up to X"
_UPPER_BOUND_RE = re.compile(
    r"(?:duoi|under|up\s+to|less\s+than|maximum|max\.?|≤|<=)\s*(\d+(?:\.\d+)?)"
    r"\s*(?:nam|years?|yr)?|[<≤]\s*(\d+(?:\.\d+)?)\s*(?:nam|years?|yr)?",
    re.IGNORECASE,
)

# Single number "X năm" / "X years"
_SINGLE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:nam|years?|yr)",
    re.IGNORECASE,
)

# Fresher / 0 năm / không yêu cầu  (NOT: any / all levels — those are null/indeterminate)
_ZERO_RE = re.compile(
    r"\b(fresher|0\s*(?:nam|years?)?|khong\s+yeu\s+cau|entry\s+level)\b",
    re.IGNORECASE,
)

# Indeterminate open-ended labels
_INDET_RE = re.compile(
    r"\b(any|all\s+levels?|n/?a|negotiable)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_experience(
    raw: Optional[str],
) -> tuple[Optional[float], Optional[float], list[str]]:
    """
    Parse raw_experience into (min_years, max_years, quality_flags).

    Returns
    -------
    (experience_min_years, experience_max_years, quality_flags)
        -1 in max_years means explicitly unbounded above.
        null means indeterminate.
    """
    flags: list[str] = []

    if not raw or not raw.strip():
        return None, None, ["MISSING_EXPERIENCE"]

    text = raw.strip()

    # --- Scraper anomaly ---
    if _is_scraper_anomaly(text):
        flags.append("SCRAPER_FIELD_MISMATCH")
        return None, None, flags

    # --- Scraper anomaly ---
    if _is_scraper_anomaly(text):
        flags.append("SCRAPER_FIELD_MISMATCH")
        return None, None, flags

    norm = _normalize(text)

    # --- Zero / Fresher (checked BEFORE seniority to catch "Fresher" correctly) ---
    if _ZERO_RE.search(norm):
        return 0.0, 0.0, flags

    # --- Indeterminate open-ended labels ---
    if _INDET_RE.search(norm):
        return None, None, flags

    # --- Seniority only ---
    if _SENIORITY_RE.match(text.strip()):
        flags.append("EXPERIENCE_LEVEL_ONLY")
        return None, None, flags

    # --- Priority 1: bounded range X-Y ---
    m = _RANGE_RE.search(norm)
    if m:
        groups = m.groups()
        # Pattern has 4 groups: (g1, g2) OR (g3, g4) depending on which alternative matched
        if groups[0] is not None:
            lo, hi = float(groups[0]), float(groups[1])
        else:
            lo, hi = float(groups[2]), float(groups[3])
        return lo, hi, flags

    # --- Priority 2: lower bound only (X+, over X) ---
    m = _LOWER_BOUND_RE.search(norm)
    if m:
        val = float(next(g for g in m.groups() if g is not None))
        return val, -1.0, flags

    # --- Priority 3: upper bound only (<X, under X) ---
    m = _UPPER_BOUND_RE.search(norm)
    if m:
        val = float(next(g for g in m.groups() if g is not None))
        return 0.0, val, flags

    # --- Priority 4: single number ---
    m = _SINGLE_RE.search(norm)
    if m:
        val = float(m.group(1))
        return val, val, flags

    # --- Fallback: unparseable ---
    flags.append("EXPERIENCE_PARSE_FAILED")
    return None, None, flags
