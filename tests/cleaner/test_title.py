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

    # ── Explicit tech-stack suffix is dropped (decision 2026-10-03 §C) ───────
    def test_title_with_tech_stack(self):
        title, flags = normalize_title("Data Engineer Python/Spark")
        assert title == "Data Engineer"
        assert "TECH_SUFFIX_REMOVED" in flags

    def test_bracketed_tech_suffix_removed(self):
        title, flags = normalize_title("Data Analyst (Azure, SQL, NoSQL, Power BI)")
        assert title == "Data Analyst"

    def test_bracket_language_requirement_removed(self):
        title, flags = normalize_title("Data Engineer (Good English)")
        assert title == "Data Engineer"

    def test_bracket_bi_tools_removed(self):
        title, flags = normalize_title("Data Analyst (BI, Power BI, SQL, Data Warehouse, ETL)")
        assert title == "Data Analyst"

    def test_bracket_with_domain_kept(self):
        title, flags = normalize_title("Senior Data Analyst (CRM & Loyalty)")
        assert title == "Data Analyst (CRM & Loyalty)"

    def test_specialisation_suffix_kept(self):
        title, flags = normalize_title("Machine Learning Engineer - Computer Vision")
        assert title == "Machine Learning Engineer - Computer Vision"
        assert "TECH_SUFFIX_REMOVED" not in flags

    def test_preserve_to_year_in_title(self):
        title, flags = normalize_title("Path to 2026 Graduate Program")
        assert title == "Path to 2026 Graduate Program"

    def test_raw_whitespace_collapsed(self):
        title, flags = normalize_title("  Data   Analyst\n")
        assert title == "Data Analyst"

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
    def test_sr_removed(self):
        title, flags = normalize_title("Sr. Data Engineer")
        assert title == "Data Engineer"

    def test_jr_removed(self):
        title, flags = normalize_title("Jr. Data Analyst")
        assert title == "Data Analyst"

    def test_mgr_expansion(self):
        title, flags = normalize_title("Data Mgr")
        assert title == "Data Manager"

    # ── Ambiguous dual roles ──────────────────────────────────────────────────
    def test_dual_role_ambiguous(self):
        title, flags = normalize_title("Data Engineer / Data Analyst")
        assert "AMBIGUOUS_TITLE" in flags
        assert "Data Engineer" in title
        assert "Data Analyst" in title

    # ── Seniority level removed (decision 2026-10-03 §C) ──────────────────────
    @pytest.mark.parametrize("raw", ["Senior Data Analyst", "Data Analyst", "DATA ANALYST"])
    def test_decision_c_examples(self, raw):
        title, flags = normalize_title(raw)
        assert title == "Data Analyst"

    def test_lead_role_kept(self):
        title, flags = normalize_title("Senior/Lead Data Engineer")
        assert title == "Lead Data Engineer"

    def test_distinct_roles_not_merged(self):
        assert normalize_title("Analytics Engineer")[0] == "Analytics Engineer"
        assert normalize_title("Machine Learning Engineer")[0] == "Machine Learning Engineer"

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

    def test_acronym_followed_by_comma_kept_upper(self):
        title, flags = normalize_title("data analyst (bi, retail)")
        assert title == "Data Analyst (BI, Retail)"

    def test_long_title_not_truncated(self):
        raw = "Data Analyst " + "Customer Insights Team " * 6
        title, flags = normalize_title(raw)
        assert "TITLE_TOO_LONG" in flags
        assert len(title) > 100


class TestTopCVTitles:
    """Tiêu đề kiểu TopCV hay kèm lương, số năm kinh nghiệm, nơi làm việc, phúc lợi."""

    @pytest.mark.parametrize("raw,expected", [
        ("Data Analyst (Từ 1 Năm Kinh Nghiệm)", "Data Analyst"),
        ("AI Engineer - Thu Nhập Hấp Dẫn Upto 40M - Tại Hà Nội", "AI Engineer"),
        ("Chuyên Viên Phân Tích Dữ Liệu Tài Chính [Hồ Chí Minh] - Thu Nhập Cạnh Tranh, Làm Việc Tại Doanh Nghiệp Top Đầu Việt Nam",
         "Chuyên Viên Phân Tích Dữ Liệu Tài Chính"),
        ("Data Lead (Lương Upto 35 Triệu)", "Data Lead"),
        ("Data Engineer (Junior-Middle)", "Data Engineer"),
        ("Data Engineer Fresher", "Data Engineer"),
        ("Senior Data Engineer (ONSITE VPBANK)", "Data Engineer"),
        ("Data Analyst (Mobile Game/ App) - Sign On Bonus 01 Tháng Lương", "Data Analyst (Mobile Game / App)"),
        ("Audit Data Analytics Specialist - ID11908", "Audit Data Analytics Specialist"),
        ("Data Engineer (Senior/Leader) English", "Data Engineer (Senior/Leader)"),
    ])
    def test_noise_removed(self, raw, expected):
        assert normalize_title(raw)[0] == expected

    def test_salary_with_trieu_not_half_cut(self):
        assert "iệu" not in normalize_title("Data Analyst Lên Tới 30 Triệu")[0]

    def test_source_casing_kept(self):
        assert normalize_title("Software Tester / QC Engineer AI-Powered Testing")[0].endswith("AI-Powered Testing")

    def test_role_word_never_stripped_away(self):
        assert normalize_title("PowerBI (Business Intelligence)")[0] == "PowerBI (Business Intelligence)"


def test_commas_kept_when_no_noise():
    assert normalize_title("Data Analyst (CRM, Loyalty), Retail")[0] == "Data Analyst (CRM, Loyalty), Retail"


def test_unbracketed_tech_list_after_role_removed():
    assert normalize_title("Data Analyst Azure, SQL, NoSQL, Power BI")[0] == "Data Analyst"
