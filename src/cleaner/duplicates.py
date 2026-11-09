"""
src/cleaner/duplicates.py
QR-05: Detect exact and near duplicates.

Rules (QR-05, report/main.tex §3.4):
- Exact duplicate: same source_url → flag later crawl_timestamp record.
- Near duplicate (ALL must hold):
    1. Same company (case-insensitive, trimmed)
    2. normalized_job_title token Jaccard ≥ 0.60
    3. Same normalized_location
    4. job_description TF-IDF cosine ≥ 0.80  ← primary gate
- Never delete duplicates; set duplicate_flag=True + duplicate_group_id.
- SENIORITY_VARIANT flag when seniority level differs but meets threshold.
- JD-only path (JD cosine ≥ 0.95 + same company, bất kể title/location) là đề xuất
  gửi Leader, CHƯA được chốt trong QR-05 → tắt mặc định (allow_jd_only=False).

The pipeline runs detect_exact_duplicates() right after QR-01 and
detect_near_duplicates() only after title/location normalization, so near-duplicate
decisions never use null normalized fields.
"""

from __future__ import annotations

import re
from typing import Optional
import math
from collections import Counter

import pandas as pd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower())) if text else set()


def _jaccard(a: Optional[str], b: Optional[str]) -> float:
    ta, tb = _tokenize(a or ""), _tokenize(b or "")
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _tf(tokens: list[str]) -> dict[str, float]:
    total = len(tokens) or 1
    c = Counter(tokens)
    return {t: cnt / total for t, cnt in c.items()}


def _build_tfidf_vectors(texts: list[str]) -> list[dict[str, float]]:
    """Compute TF-IDF vectors for a corpus of texts."""
    tokenized = [re.findall(r"[a-z0-9]+", (t or "").lower()) for t in texts]
    n = len(texts)
    df: Counter = Counter()
    for toks in tokenized:
        for tok in set(toks):
            df[tok] += 1

    def idf(tok: str) -> float:
        return math.log((n + 1) / (df[tok] + 1)) + 1

    vectors = []
    for toks in tokenized:
        tf_map = _tf(toks)
        vectors.append({tok: tf_map[tok] * idf(tok) for tok in tf_map})
    return vectors


def _cosine(v1: dict[str, float], v2: dict[str, float]) -> float:
    common = set(v1) & set(v2)
    dot = sum(v1[t] * v2[t] for t in common)
    mag1 = math.sqrt(sum(x * x for x in v1.values()))
    mag2 = math.sqrt(sum(x * x for x in v2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


_SENIORITY_TOKENS = {"senior", "sr", "lead", "principal", "junior", "jr", "mid", "staff"}


def _has_seniority_diff(title_a: Optional[str], title_b: Optional[str]) -> bool:
    """True if one title has a seniority token that the other does not."""
    ta = _tokenize(title_a or "")
    tb = _tokenize(title_b or "")
    return bool((ta & _SENIORITY_TOKENS) ^ (tb & _SENIORITY_TOKENS))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

NEAR_DUP_TITLE_JACCARD = 0.60
NEAR_DUP_JD_COSINE = 0.80
HIGH_CONF_JD_COSINE = 0.95  # JD-only path — đề xuất gửi Leader, chưa thuộc QR-05


def _ensure_columns(df: pd.DataFrame) -> None:
    if "duplicate_flag" not in df.columns:
        df["duplicate_flag"] = False
    df["duplicate_flag"] = df["duplicate_flag"].map(lambda v: bool(v) if v is not None and v == v else False)
    if "duplicate_group_id" not in df.columns:
        df["duplicate_group_id"] = None
    if "quality_flags" not in df.columns:
        df["quality_flags"] = [[] for _ in range(len(df))]


def _add_flag(df: pd.DataFrame, i, flag: str) -> None:
    flags = list(df.at[i, "quality_flags"] or [])
    if flag not in flags:
        flags.append(flag)
    df.at[i, "quality_flags"] = flags


def detect_exact_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """QR-05a: same source_url → flag every record after the first one.

    The record kept as canonical is the earliest by crawl_timestamp (ties: input order).
    """
    _ensure_columns(df)
    has_ts = "crawl_timestamp" in df.columns
    # Stable sort: missing timestamps go last, ties keep input order.
    order = sorted(df.index, key=lambda i: str(df.at[i, "crawl_timestamp"] or "\uffff") if has_ts else "")
    url_seen: dict[str, str] = {}
    for i in order:
        url = (df.at[i, "source_url"] or "").strip()
        if not url:
            continue
        if url in url_seen:
            df.at[i, "duplicate_flag"] = True
            df.at[i, "duplicate_group_id"] = url_seen[url]
            _add_flag(df, i, "DUPLICATE_EXACT")
        else:
            url_seen[url] = df.at[i, "job_id"]
    return df


def detect_near_duplicates(df: pd.DataFrame, *, allow_jd_only: bool = False) -> pd.DataFrame:
    """QR-05b: all four conditions must hold for a near duplicate:

    same company, normalized_job_title Jaccard ≥ 0.60, same normalized_location,
    job_description TF-IDF cosine ≥ 0.80.

    Requires normalized_job_title / normalized_location to be filled already.
    ``allow_jd_only=True`` additionally enables the proposed JD-only path
    (JD cosine ≥ 0.95 + same company); keep it off until the Leader approves it.
    """
    _ensure_columns(df)
    for col in ("normalized_job_title", "normalized_location"):
        if col not in df.columns:
            raise ValueError(f"detect_near_duplicates cần cột {col}; chạy QR-02/QR-04 trước")

    jd_texts = list(df["job_description"].fillna(""))
    tfidf_vecs = _build_tfidf_vectors(jd_texts)

    n = len(df)
    indices = df.index.tolist()

    for a_pos in range(n):
        i = indices[a_pos]
        if df.at[i, "duplicate_flag"]:
            continue

        comp_a = (df.at[i, "company"] or "").strip().lower()
        loc_a = df.at[i, "normalized_location"]
        title_a = df.at[i, "normalized_job_title"]

        for b_pos in range(a_pos + 1, n):
            j = indices[b_pos]
            if df.at[j, "duplicate_flag"]:
                continue

            comp_b = (df.at[j, "company"] or "").strip().lower()
            if comp_a != comp_b or not comp_a:
                continue

            title_b = df.at[j, "normalized_job_title"]
            loc_b = df.at[j, "normalized_location"]
            jd_cos = _cosine(tfidf_vecs[a_pos], tfidf_vecs[b_pos])

            standard = (
                bool(title_a) and bool(title_b)
                and _jaccard(title_a, title_b) >= NEAR_DUP_TITLE_JACCARD
                and loc_a == loc_b
                and jd_cos >= NEAR_DUP_JD_COSINE
            )
            jd_only = allow_jd_only and not standard and jd_cos >= HIGH_CONF_JD_COSINE
            if not (standard or jd_only):
                continue

            df.at[j, "duplicate_flag"] = True
            df.at[j, "duplicate_group_id"] = df.at[i, "job_id"]
            _add_flag(df, j, "DUPLICATE_NEAR")
            if jd_only:
                _add_flag(df, j, "HIGH_CONF_JD_ONLY")
            if _has_seniority_diff(title_a, title_b):
                _add_flag(df, j, "SENIORITY_VARIANT")

    return df


def detect_duplicates(df: pd.DataFrame, *, allow_jd_only: bool = False) -> pd.DataFrame:
    """Run QR-05a then QR-05b. Normalized title/location must already be present."""
    detect_exact_duplicates(df)
    return detect_near_duplicates(df, allow_jd_only=allow_jd_only)
