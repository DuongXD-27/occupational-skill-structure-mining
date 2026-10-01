"""
src/cleaner/relevance.py
QR-06: Classify job posting as Data/AI-relevant or not.

Decision flow (from docs/data_cleaning/data_quality_rules.md §7.7):
  Step 1 — Exclusion Title Gate (run FIRST):
      If normalized_job_title matches exclusion patterns → relevance_flag=false.
  Step 2 — Whitelist Check (only if not excluded in Step 1):
      Scan raw_job_title, job_description, job_requirements for core keywords.
      If any match → relevance_flag=true.
  Step 3 — Explicit default:
      If neither list matches → relevance_flag=true + MANUAL_REVIEW_REQUIRED.
  Step 4 — Text quality check:
      If job_description < 50 chars → DESCRIPTION_TOO_SHORT.
      If both fields < 50 chars → exclusion_reason=INSUFFICIENT_TEXT.

Also implements QR-01 §2.2 / §2.4 missing-value and scrape-error handling.
"""

from __future__ import annotations

import re
from typing import Optional

# ---------------------------------------------------------------------------
# Step 1: Exclusion patterns  (applied to normalized_job_title, case-insensitive)
# Each tuple: (regex_pattern, exclusion_reason)
# ---------------------------------------------------------------------------

_EXCLUSION_RULES: list[tuple[re.Pattern, str]] = [
    # Data Entry (checked before generic IT to catch "data input" correctly)
    (re.compile(r"\b(data\s+entry|data\s+input|nh[aậ]p\s+li[eệ]u)\b", re.IGNORECASE), "DATA_ENTRY_ROLE"),

    # Pure IT – no Data/AI
    (re.compile(
        r"\b(software\s+engineer(?!\s+(ai|ml|data))|web\s+developer|front[\s-]?end\s+developer|"
        r"back[\s-]?end\s+developer|mobile\s+developer|android\s+developer|ios\s+developer|"
        r"devops\s+engineer|site\s+reliability|sre\b|system\s+admin|sysadmin|"
        r"network\s+engineer|qa\s+engineer|quality\s+assurance|tester\b|"
        r"sap\s+(specialist|mm|fico|hcm|sd|pp|wm|consultant)|erp\s+consultant)\b",
        re.IGNORECASE), "NOT_DATA_AI_ROLE"),

    # Sales / Marketing / HR
    (re.compile(
        r"\b(sales\s+(executive|manager|representative|engineer)?|"
        r"marketing\s+(manager|executive|specialist)?|"
        r"business\s+development|account\s+manager|"
        r"human\s+resources|hr\s+(manager|executive|specialist)|recruiter|"
        r"talent\s+acquisition|monetization\s+specialist|"
        r"growth\s+hacker|brand\s+manager)\b",
        re.IGNORECASE), "NOT_DATA_AI_ROLE"),

    # Finance / Operations / Legal
    (re.compile(
        r"\b(accountant|chief\s+accountant|financial\s+analyst(?!\s+data)|"
        r"logistics|supply\s+chain|operations\s+manager|"
        r"legal\s+counsel|compliance\s+officer|paralegal)\b",
        re.IGNORECASE), "NOT_DATA_AI_ROLE"),

    # Design
    (re.compile(
        r"\b(ui/ux\s+designer|graphic\s+designer|visual\s+designer|"
        r"product\s+designer(?!\s+(ai|data))|illustrator|animator)\b",
        re.IGNORECASE), "NOT_DATA_AI_ROLE"),

    # General management / Scholarship
    (re.compile(
        r"\b(general\s+manager|chief\s+executive|ceo\b|coo\b|"
        r"project\s+manager(?!\s+(data|ai|ml))|program\s+manager(?!\s+(data|ai))|"
        r"scholarship|internship\s+(ba|qa)\b)\b",
        re.IGNORECASE), "NOT_DATA_AI_ROLE"),
]

# ---------------------------------------------------------------------------
# Step 2: Whitelist keywords (scan title + JD + requirements)
# ---------------------------------------------------------------------------

_WHITELIST_KEYWORDS = [
    # Languages / frameworks
    "python", "r language", "sql", "spark", "hadoop", "kafka", "airflow", "dbt",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
    # AI/ML concepts
    "machine learning", "deep learning", "neural network", "nlp", "llm", "gpt",
    "computer vision", "data pipeline", "etl", "elt", "data warehouse", "data lake",
    # BI tools
    "power bi", "tableau", "looker", "metabase", "superset",
    # Job family titles
    "data analyst", "data engineer", "data scientist", "data architect",
    "bi analyst", "analytics engineer", "mlops", "llmops",
    # Modern AI
    "vector database", "embedding", "rag", "fine-tuning", "fine tuning",
    # Statistics
    "statistics", "regression", "classification", "clustering",
    "recommendation system", "recommendation engine",
    # Broad data
    "data analysis", "data mining", "data science", "data quality",
    "feature engineering", "model training", "model deployment",
    "business intelligence", "business analytics",
]

# Pre-compile for speed (word-boundary aware where possible)
_WHITELIST_RE = re.compile(
    "|".join(
        r"\b" + re.escape(kw) + r"\b"
        for kw in sorted(_WHITELIST_KEYWORDS, key=len, reverse=True)  # longest first
    ),
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_relevance(
    normalized_job_title: Optional[str],
    raw_job_title: Optional[str],
    job_description: Optional[str],
    job_requirements: Optional[str],
) -> tuple[bool, Optional[str], list[str]]:
    """
    Classify a job posting for Data/AI relevance.

    Returns
    -------
    (relevance_flag, exclusion_reason, quality_flags)
        relevance_flag   : bool
        exclusion_reason : str | None
        quality_flags    : list[str]
    """
    flags: list[str] = []
    jd = (job_description or "").strip()
    jr = (job_requirements or "").strip()
    title_norm = (normalized_job_title or "").strip()
    title_raw = (raw_job_title or "").strip()

    # --- QR-01 §2.2: both text fields absent ---
    if not jd and not jr:
        return False, "INSUFFICIENT_TEXT", ["MISSING_TEXT_FIELDS"]

    # --- QR-01 §2.4: both text fields too short ---
    if len(jd) < 30 and len(jr) < 30:
        return False, "SCRAPE_ERROR", ["SCRAPE_FAILED"]

    # --- Step 4 pre-check: short description ---
    if len(jd) < 50:
        flags.append("DESCRIPTION_TOO_SHORT")

    # --- Step 1: Exclusion Title Gate ---
    check_title = title_norm or title_raw
    for exclusion_pattern, reason in _EXCLUSION_RULES:
        if check_title and exclusion_pattern.search(check_title):
            # Check for ambiguous titles (Data/AI token + exclusion token)
            if _WHITELIST_RE.search(check_title):
                flags.append("AMBIGUOUS_CLASSIFICATION")
            return False, reason, flags

    # --- Step 2: Whitelist Check ---
    combined = " ".join([title_raw, jd, jr])
    if _WHITELIST_RE.search(combined):
        return True, None, flags

    # --- Step 3: Explicit default — retain, flag for manual review ---
    flags.append("MANUAL_REVIEW_REQUIRED")
    return True, None, flags
