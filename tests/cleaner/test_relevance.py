"""
tests/cleaner/test_relevance.py
QR-06 relevance classification tests.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest
from cleaner.relevance import classify_relevance

# Helper JD/JR text samples
_ML_JD = (
    "This role involves training machine learning models using PyTorch and TensorFlow. "
    "You will work on computer vision pipelines and deep learning architectures. "
    "Experience with Python, pandas, and scikit-learn is required."
)
_ML_JR = (
    "Requirements: 3+ years in machine learning or deep learning. "
    "Strong Python skills. Familiarity with MLOps practices."
)

_MARKETING_JD = (
    "We are looking for a marketing specialist to drive growth campaigns. "
    "You will manage social media, email marketing, and paid ad campaigns. "
    "Experience with Google Analytics and Facebook Ads Manager required."
)
_MARKETING_JD_WITH_SQL = (
    "We are looking for an Advertising Monetization Specialist. "
    "You will optimize ad revenue using SQL, API, or coding knowledge. "
    "Experience with Google Ad Manager required."
)

_BACKEND_JD = (
    "Looking for a backend developer to build REST APIs using Node.js and PostgreSQL. "
    "You will design microservices and maintain CI/CD pipelines."
)
_BACKEND_JR = (
    "Requirements: 2+ years backend development. Proficiency in Node.js, Express.js. "
    "Knowledge of Docker and Kubernetes preferred."
)

_DATA_ENTRY_JD = (
    "Input data from physical documents into the company system. "
    "Check data accuracy. No programming required."
)


class TestClassifyRelevance:
    # ── Clearly relevant Data/AI roles ───────────────────────────────────────
    def test_ml_engineer_relevant(self):
        flag, reason, flags = classify_relevance(
            "Machine Learning Engineer", "Machine Learning Engineer",
            _ML_JD, _ML_JR,
        )
        assert flag is True
        assert reason is None

    def test_data_analyst_relevant(self):
        flag, reason, flags = classify_relevance(
            "Data Analyst", "Data Analyst",
            "Analyze data using SQL and Python. Build Tableau dashboards.",
            "SQL, Python, Excel required.",
        )
        assert flag is True

    def test_data_engineer_relevant(self):
        flag, reason, flags = classify_relevance(
            "Data Engineer", "Data Engineer",
            "Build ETL pipelines using Airflow, Spark, and dbt.",
            "3+ years experience with Spark, Hadoop.",
        )
        assert flag is True

    # ── Out-of-scope: title-gate exclusions ──────────────────────────────────
    def test_out_of_scope_sap(self):
        flag, reason, flags = classify_relevance(
            "Senior SAP Specialist", "Senior SAP Specialist",
            "Configure and maintain SAP ERP system.", "SAP MM/FI experience required.",
        )
        assert flag is False
        assert reason == "NOT_DATA_AI_ROLE"

    def test_out_of_scope_scholarship(self):
        flag, reason, flags = classify_relevance(
            "VPBank Scholarship", "VPBank Scholarship",
            "Apply for our annual scholarship program.", "GPA > 3.5 required.",
        )
        assert flag is False
        assert reason == "NOT_DATA_AI_ROLE"

    def test_out_of_scope_monetization(self):
        """Critical: Advertising Monetization Specialist must NOT be kept
        even when job_requirements contains SQL/API keywords."""
        flag, reason, flags = classify_relevance(
            "Advertising Monetization Specialist",
            "Advertising Monetization Specialist",
            _MARKETING_JD_WITH_SQL,
            "SQL, API, or coding knowledge is a plus. AdOps experience required.",
        )
        assert flag is False
        assert reason == "NOT_DATA_AI_ROLE"

    def test_out_of_scope_backend_developer(self):
        """Backend Developer with Python in JD should NOT be auto-included."""
        flag, reason, flags = classify_relevance(
            "Backend Developer - Python", "Backend Developer - Python",
            _BACKEND_JD, _BACKEND_JR,
        )
        assert flag is False
        assert reason == "NOT_DATA_AI_ROLE"

    def test_out_of_scope_data_entry(self):
        flag, reason, flags = classify_relevance(
            "Data Entry Specialist", "Data Entry Specialist",
            _DATA_ENTRY_JD, "Fast typing. Attention to detail.",
        )
        assert flag is False
        assert reason == "DATA_ENTRY_ROLE"

    def test_out_of_scope_qa_internship(self):
        flag, reason, flags = classify_relevance(
            "Internship BA/QA", "Internship BA/QA",
            "Testing software applications. Writing test cases.",
            "Basic programming knowledge.",
        )
        assert flag is False
        assert reason == "NOT_DATA_AI_ROLE"

    # ── Boundary: whitelist keyword in JD but title is a clear Data/AI role ──
    def test_ml_engineer_with_python_in_jd(self):
        flag, reason, flags = classify_relevance(
            "Machine Learning Engineer", "Machine Learning Engineer",
            "Use Python and PyTorch to train models.", "3+ years ML experience.",
        )
        assert flag is True

    # ── Missing / insufficient text ───────────────────────────────────────────
    def test_both_text_missing(self):
        flag, reason, flags = classify_relevance(
            "Data Analyst", "Data Analyst", None, None,
        )
        assert flag is False
        assert reason == "INSUFFICIENT_TEXT"

    def test_both_text_empty(self):
        flag, reason, flags = classify_relevance(
            "Data Analyst", "Data Analyst", "", "",
        )
        assert flag is False
        assert reason == "INSUFFICIENT_TEXT"

    def test_both_text_too_short(self):
        flag, reason, flags = classify_relevance(
            "Data Analyst", "Data Analyst", "Short.", "Short.",
        )
        assert flag is False
        assert reason == "SCRAPE_ERROR"

    # ── Unknown role → retain with manual review flag ─────────────────────────
    def test_unknown_role_manual_review(self):
        flag, reason, flags = classify_relevance(
            "Wizard", "Wizard",
            "Doing wizard things at the office.", "Must be magical.",
        )
        assert flag is True
        assert "MANUAL_REVIEW_REQUIRED" in flags

    # ── Internship/Fresher Data role must be retained ─────────────────────────
    def test_intern_data_role_kept(self):
        flag, reason, flags = classify_relevance(
            "Fresher Data Analyst", "Fresher Data Analyst",
            "Analyze data using SQL and Python.", "Fresher or 0-1 year experience.",
        )
        assert flag is True
