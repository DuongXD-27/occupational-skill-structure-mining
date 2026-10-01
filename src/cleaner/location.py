"""
src/cleaner/location.py
QR-02: Normalize raw_location → normalized_location

Rules (from docs/data_cleaning/data_quality_rules.md §3):
- raw_location is immutable; output goes to normalized_location.
- Mapping driven by docs/data_cleaning/location_mapping.csv (no hardcoded if/else chains).
- Placeholder strings (Not Available, N/A) → null + flag MISSING_LOCATION.
- Multi-location (comma/slash between different regions) → "Nhiều địa điểm".
- Unrecognized → null + flag LOCATION_UNRECOGNIZED.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Load mapping table at import time (single source of truth)
# ---------------------------------------------------------------------------

_MAPPING_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "data_cleaning"
    / "location_mapping.csv"
)

# List of (compiled_pattern, normalized_value) tuples, in file order.
_LOCATION_RULES: list[tuple[re.Pattern, str]] = []

def _load_mapping(path: Path = _MAPPING_PATH) -> None:
    """Read location_mapping.csv and compile regex patterns."""
    _LOCATION_RULES.clear()
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_pattern = row["raw_pattern"].strip()
            normalized = row["normalized_location"].strip()
            compiled = re.compile(raw_pattern, re.IGNORECASE)
            _LOCATION_RULES.append((compiled, normalized))


_load_mapping()

# Placeholder patterns that should map to null
_PLACEHOLDER_RE = re.compile(
    r"^\s*(not\s+available|n/?a|unknown|none|-)\s*$", re.IGNORECASE
)
# Detects pure "Not Available" tokens inside a multi-part string
_NA_TOKEN_RE = re.compile(r"not\s+available", re.IGNORECASE)


def normalize_location(raw: Optional[str]) -> tuple[Optional[str], list[str]]:
    """
    Normalize a raw_location string.

    Returns
    -------
    (normalized_location, quality_flags)
        normalized_location : str | None
        quality_flags       : list[str]  — may contain MISSING_LOCATION,
                              LOCATION_UNRECOGNIZED, MULTI_LOCATION
    """
    flags: list[str] = []

    if not raw or not raw.strip():
        return None, ["MISSING_LOCATION"]

    text = raw.strip()

    # --- Step 1: pure placeholder? ---
    if _PLACEHOLDER_RE.match(text):
        return None, ["MISSING_LOCATION"]

    # --- Step 2: split multi-part strings (comma or slash) ---
    # Remove all NA tokens first so they don't count as real parts
    cleaned_for_split = _NA_TOKEN_RE.sub("", text)
    parts = [p.strip() for p in re.split(r"[,/]", cleaned_for_split) if p.strip()]

    # Resolve each meaningful part independently
    resolved: list[str] = []
    for part in parts:
        match_result = _match_single(part)
        if match_result:
            resolved.append(match_result)

    # Determine if original string had NA tokens (adds MISSING_LOCATION)
    had_na = bool(_NA_TOKEN_RE.search(text))

    unique_resolved = list(dict.fromkeys(resolved))  # preserve order, dedupe

    if not unique_resolved:
        # Nothing recognized
        if had_na:
            return None, ["MISSING_LOCATION"]
        return None, ["LOCATION_UNRECOGNIZED"]

    if len(unique_resolved) == 1:
        result = unique_resolved[0]
        if had_na:
            flags.append("MISSING_LOCATION")
        return result, flags

    # Multiple distinct cities/regions
    flags.append("MULTI_LOCATION")
    if had_na:
        flags.append("MISSING_LOCATION")
    return "Nhiều địa điểm", flags


def _match_single(text: str) -> Optional[str]:
    """Match a single location token against the mapping table. Returns None if unrecognized."""
    text = text.strip()
    if not text:
        return None
    for pattern, normalized in _LOCATION_RULES:
        if pattern.search(text):
            return normalized
    return None
