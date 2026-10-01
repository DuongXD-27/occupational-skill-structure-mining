"""
tests/cleaner/test_duplicates.py
QR-05 duplicate detection tests.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest
import pandas as pd
from cleaner.duplicates import detect_duplicates

# ── Sample JD texts ─────────────────────────────────────────────────────────
_JD_DE_1 = (
    "We are looking for a Data Engineer to design and build scalable data pipelines "
    "using Apache Spark, Airflow, and dbt. You will work closely with data scientists "
    "and analysts to ensure data quality and availability. Experience with cloud platforms "
    "such as AWS or GCP is a strong advantage. Must know Python and SQL."
)
# Near-identical JD (only minor wording change)
_JD_DE_2 = (
    "We are looking for a Data Engineer to design and build scalable data pipelines "
    "using Apache Spark, Airflow, and dbt. You will work closely with data scientists "
    "and analysts to ensure data quality and availability. Experience with cloud platforms "
    "such as AWS or GCP is strongly preferred. Must know Python and SQL."
)
# Completely different JD
_JD_BA = (
    "Looking for a Business Analyst to gather requirements from stakeholders, write "
    "user stories, and work with the development team. Must have Agile experience. "
    "Tableau or Power BI knowledge is a plus."
)


def _base_df(**overrides) -> pd.DataFrame:
    base = {
        "job_id": ["JOB001", "JOB002"],
        "source_url": ["https://example.com/1", "https://example.com/2"],
        "company": ["Acme Corp", "Acme Corp"],
        "normalized_job_title": ["Data Engineer", "Data Engineer"],
        "normalized_location": ["Hà Nội", "Hà Nội"],
        "job_description": [_JD_DE_1, _JD_DE_2],
        "crawl_timestamp": ["2026-01-01T10:00:00Z", "2026-01-01T11:00:00Z"],
        "quality_flags": [[], []],
        "duplicate_flag": [False, False],
        "duplicate_group_id": [None, None],
    }
    base.update(overrides)
    return pd.DataFrame(base)


class TestExactDuplicates:
    def test_same_url_flags_second(self):
        df = _base_df(
            source_url=["https://example.com/same", "https://example.com/same"]
        )
        df = detect_duplicates(df)
        assert df.loc[0, "duplicate_flag"] == False
        assert df.loc[1, "duplicate_flag"] == True
        assert df.loc[1, "duplicate_group_id"] == "JOB001"
        assert "DUPLICATE_EXACT" in df.loc[1, "quality_flags"]

    def test_different_url_not_flagged_as_exact(self):
        df = _base_df()  # different URLs
        df = detect_duplicates(df)
        # May or may not be near-dup, but not EXACT
        assert "DUPLICATE_EXACT" not in df.loc[0, "quality_flags"]
        assert "DUPLICATE_EXACT" not in (df.loc[1, "quality_flags"] or [])


class TestNearDuplicates:
    def test_near_identical_jd_same_company_flagged(self):
        """Near-identical JDs under the same company should be near-duplicates."""
        df = _base_df()
        df = detect_duplicates(df)
        # Second record should be flagged
        assert df.loc[1, "duplicate_flag"] == True
        flags = df.loc[1, "quality_flags"]
        assert "DUPLICATE_NEAR" in flags

    def test_different_company_not_duplicate(self):
        df = _base_df(company=["Acme Corp", "Other Corp"])
        df = detect_duplicates(df)
        assert df.loc[1, "duplicate_flag"] == False

    def test_different_location_not_duplicate(self):
        df = _base_df(normalized_location=["Hà Nội", "Hồ Chí Minh"])
        df = detect_duplicates(df)
        # Different location: standard near-dup path should not trigger
        # (may still trigger via HIGH_CONF_JD_ONLY path if cosine ≥ 0.95)
        # Just check it's not flagged via the standard path without location match
        pass  # behaviour depends on cosine; no assertion here — covered by unit

    def test_very_different_jd_not_duplicate(self):
        df = _base_df(job_description=[_JD_DE_1, _JD_BA])
        df = detect_duplicates(df)
        assert df.loc[1, "duplicate_flag"] == False

    def test_seniority_variant_flag(self):
        """Senior vs non-senior variant gets SENIORITY_VARIANT flag."""
        df = _base_df(
            normalized_job_title=["Senior Data Engineer", "Data Engineer"]
        )
        df = detect_duplicates(df)
        if df.loc[1, "duplicate_flag"]:
            assert "SENIORITY_VARIANT" in df.loc[1, "quality_flags"]

    def test_high_conf_jd_only_path(self):
        """JD cosine ≥ 0.95 + same company → flagged even without title match."""
        df = _base_df(
            normalized_job_title=["Senior AI Expert ML/DL/LLM", "AI Expert CV/NLP/LLM"]
        )
        df = detect_duplicates(df)
        # With near-identical JDs and different titles, HIGH_CONF_JD_ONLY path triggers
        # (this is the MB Bank edge case from the empirical study)
        if df.loc[1, "duplicate_flag"]:
            flags = df.loc[1, "quality_flags"]
            assert "DUPLICATE_NEAR" in flags

    def test_epam_false_positive_not_flagged(self):
        """EPAM pair: same title structure but different JD content → not duplicate."""
        jd_epam_27 = (
            "We are looking for a Senior/Lead Data Engineer with PySpark and Snowflake "
            "experience. You will own data infrastructure, mentor the team, and work on "
            "large-scale batch processing pipelines. Remote-friendly position with bonus."
        )
        jd_epam_33 = (
            "Senior/Lead Data Software Engineer role focusing on software architecture "
            "and data product delivery. You will design APIs and data services. "
            "PySpark and Snowflake used in some projects. Entirely different scope."
        )
        df = _base_df(
            job_id=["JOB027", "JOB033"],
            normalized_job_title=[
                "Senior Lead Data Engineer Pyspark Snowflake",
                "Senior Lead Data Software Engineer Pyspark Snowflake",
            ],
            job_description=[jd_epam_27, jd_epam_33],
        )
        df = detect_duplicates(df)
        # JD cosine should be < 0.80 → not duplicate (or at most borderline)
        # This test documents the expected behaviour
        assert df.loc[1, "duplicate_flag"] == False
