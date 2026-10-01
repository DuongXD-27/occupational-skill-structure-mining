"""
tests/cleaner/test_experience.py
QR-03 experience parsing tests.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest
from cleaner.experience import parse_experience


class TestParseExperience:
    # ── Range ────────────────────────────────────────────────────────────────
    def test_range_years(self):
        mn, mx, flags = parse_experience("3-5 years")
        assert mn == 3.0 and mx == 5.0 and not flags

    def test_range_vietnamese(self):
        mn, mx, flags = parse_experience("1 - 3 năm")
        assert mn == 1.0 and mx == 3.0

    def test_range_tu_den(self):
        mn, mx, flags = parse_experience("từ 2 đến 4 năm")
        assert mn == 2.0 and mx == 4.0

    # ── Lower bound only (min known, upper unbounded) ────────────────────────
    def test_at_least_2(self):
        mn, mx, flags = parse_experience("At least 2 years")
        assert mn == 2.0 and mx == -1.0

    def test_over_3(self):
        mn, mx, flags = parse_experience("Over 3 years")
        assert mn == 3.0 and mx == -1.0

    def test_2_plus(self):
        mn, mx, flags = parse_experience("2+ years")
        assert mn == 2.0 and mx == -1.0

    def test_greater_than(self):
        mn, mx, flags = parse_experience(">2 năm")
        assert mn == 2.0 and mx == -1.0

    # ── Upper bound only ─────────────────────────────────────────────────────
    def test_under_1(self):
        mn, mx, flags = parse_experience("Dưới 1 năm")
        assert mn == 0.0 and mx == 1.0

    def test_less_than(self):
        mn, mx, flags = parse_experience("< 1 year")
        assert mn == 0.0 and mx == 1.0

    # ── Single number ────────────────────────────────────────────────────────
    def test_single_year(self):
        mn, mx, flags = parse_experience("3 năm")
        assert mn == 3.0 and mx == 3.0

    def test_single_years(self):
        mn, mx, flags = parse_experience("5 years")
        assert mn == 5.0 and mx == 5.0

    # ── Fresher / zero ───────────────────────────────────────────────────────
    def test_fresher(self):
        mn, mx, flags = parse_experience("Fresher")
        assert mn == 0.0 and mx == 0.0

    def test_zero_nam(self):
        mn, mx, flags = parse_experience("0 năm")
        assert mn == 0.0 and mx == 0.0

    def test_khong_yeu_cau(self):
        mn, mx, flags = parse_experience("Không yêu cầu")
        assert mn == 0.0 and mx == 0.0

    # ── Indeterminate ────────────────────────────────────────────────────────
    def test_any(self):
        mn, mx, flags = parse_experience("Any")
        assert mn is None and mx is None

    def test_all_levels(self):
        mn, mx, flags = parse_experience("All levels")
        assert mn is None and mx is None

    def test_null_input(self):
        mn, mx, flags = parse_experience(None)
        assert mn is None and mx is None
        assert "MISSING_EXPERIENCE" in flags

    # ── Invalid / unparseable ────────────────────────────────────────────────
    def test_invalid_string(self):
        mn, mx, flags = parse_experience("Open")
        assert mn is None and mx is None
        assert "EXPERIENCE_PARSE_FAILED" in flags

    # ── Seniority levels (no numbers) ────────────────────────────────────────
    def test_senior_label(self):
        mn, mx, flags = parse_experience("Senior")
        assert mn is None and mx is None
        assert "EXPERIENCE_LEVEL_ONLY" in flags

    def test_junior_label(self):
        mn, mx, flags = parse_experience("Junior")
        assert mn is None and mx is None
        assert "EXPERIENCE_LEVEL_ONLY" in flags

    def test_mid_level(self):
        mn, mx, flags = parse_experience("Mid-level")
        assert mn is None and mx is None
        assert "EXPERIENCE_LEVEL_ONLY" in flags

    # ── Scraper anomalies ────────────────────────────────────────────────────
    def test_at_office(self):
        mn, mx, flags = parse_experience("At office")
        assert mn is None and mx is None
        assert "SCRAPER_FIELD_MISMATCH" in flags

    def test_hybrid(self):
        mn, mx, flags = parse_experience("Hybrid")
        assert mn is None and mx is None
        assert "SCRAPER_FIELD_MISMATCH" in flags

    def test_hybrid_with_address(self):
        mn, mx, flags = parse_experience(
            "Hybrid, Dolphin Plaza, 6 Nguyen Hoang Street, 3rd floor"
        )
        assert mn is None and mx is None
        assert "SCRAPER_FIELD_MISMATCH" in flags

    def test_remote_da_nang(self):
        mn, mx, flags = parse_experience("Remote, Da Nang")
        assert mn is None and mx is None
        assert "SCRAPER_FIELD_MISMATCH" in flags

    def test_street_address(self):
        mn, mx, flags = parse_experience("174 Thai Ha, Dong Da, Ha Noi")
        assert mn is None and mx is None
        assert "SCRAPER_FIELD_MISMATCH" in flags
