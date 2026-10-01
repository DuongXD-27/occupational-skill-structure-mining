"""
tests/cleaner/test_title.py
QR-04 job title normalization tests.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest
from cleaner.title import normalize_title


class TestNormalizeTitle:
    # ── Uppercase / lowercase ─────────────────────────────────────────────────
    def test_all_caps(self):
        title, flags = normalize_title("DATA ANALYST")
        assert title == "Data Analyst"
        assert not flags

    def test_mixed_case(self):
        title, flags = normalize_title("data engineer")
        assert title == "Data Engineer"

    # ── Title with tech stack in it (preserve) ───────────────────────────────
    def test_title_with_tech_stack(self):
        title, flags = normalize_title("Data Engineer Python/Spark")
        assert title == "Data Engineer Python/Spark"

    def test_title_cpp(self):
        # C++ must not be broken
        title, flags = normalize_title("C++ Developer")
        assert "C++" in title

    # ── Salary noise ─────────────────────────────────────────────────────────
    def test_strip_salary(self):
        title, flags = normalize_title("Data Analyst Up to 75M")
        assert "75M" not in title
        assert "Data Analyst" in title

    # ── Bonus noise ───────────────────────────────────────────────────────────
    def test_strip_bonus(self):
        title, flags = normalize_title("Data Engineer - BONUS")
        assert "BONUS" not in title

    # ── Trailing syntax ───────────────────────────────────────────────────────
    def test_trailing_slash(self):
        title, flags = normalize_title("Data Analyst /")
        assert not title.endswith("/")

    def test_trailing_comma(self):
        title, flags = normalize_title("Backend Developer,")
        assert not title.endswith(",")

    # ── English required suffix ───────────────────────────────────────────────
    def test_english_required(self):
        title, flags = normalize_title("Data Analyst, English required /")
        assert "English required" not in title

    # ── Abbreviation expansion ────────────────────────────────────────────────
    def test_sr_expansion(self):
        title, flags = normalize_title("Sr. Data Engineer")
        assert title.startswith("Senior")

    def test_jr_expansion(self):
        title, flags = normalize_title("Jr. Data Analyst")
        assert title.startswith("Junior")

    # ── Ambiguous dual roles ──────────────────────────────────────────────────
    def test_dual_role_ambiguous(self):
        title, flags = normalize_title("Data Engineer / Data Analyst")
        assert "AMBIGUOUS_TITLE" in flags
        assert "Data Engineer" in title
        assert "Data Analyst" in title

    # ── Senior must NOT be stripped ───────────────────────────────────────────
    def test_senior_preserved(self):
        title, flags = normalize_title("Senior Data Analyst")
        assert "Senior" in title

    def test_senior_data_analyst_not_merged(self):
        # Senior Data Analyst ≠ Data Analyst (must not be stripped to Data Analyst)
        title, flags = normalize_title("Senior Data Analyst")
        assert title == "Senior Data Analyst"

    # ── Too short ─────────────────────────────────────────────────────────────
    def test_too_short(self):
        title, flags = normalize_title("AI")
        assert "TITLE_TOO_SHORT" in flags

    # ── Typo preserved in normalized form (only surface noise removed) ────────
    def test_typo_preserved_structure(self):
        # Typos in actual role names are NOT corrected by QR-04
        title, flags = normalize_title("Appllication/Intergration Engineer")
        assert title is not None
        assert len(title) > 0

    # ── None input ────────────────────────────────────────────────────────────
    def test_none_input(self):
        title, flags = normalize_title(None)
        assert title is None
        assert "MISSING_JOB_TITLE" in flags

    # ── Known acronyms stay uppercase ────────────────────────────────────────
    def test_sql_uppercase(self):
        title, flags = normalize_title("sql developer")
        assert "SQL" in title

    def test_bi_uppercase(self):
        title, flags = normalize_title("bi analyst")
        assert "BI" in title
