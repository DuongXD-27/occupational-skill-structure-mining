"""
src/cleaner/duplicates.py
QR-05: Detect exact and near duplicates.

Rules (from docs/data_cleaning/data_quality_rules.md §6):
- Exact duplicate: same source_url → flag later crawl_timestamp record.
- Near duplicate (ALL must hold):
    1. Same company (case-insensitive, trimmed)
    2. normalized_job_title token Jaccard ≥ 0.60
    3. Same normalized_location
    4. job_description TF-IDF cosine ≥ 0.80  ← primary gate
- Never delete duplicates; set duplicate_flag=True + duplicate_group_id.
- SENIORITY_VARIANT flag when seniority level differs but meets threshold.
- High-confidence JD-only path: JD cosine ≥ 0.95 + same company (Leader proposal).
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
HIGH_CONF_JD_COSINE = 0.95  # JD-only path (Leader proposal)


def detect_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add duplicate_flag, duplicate_group_id, and quality_flags columns to df.

    Expects columns: job_id, source_url, company, normalized_job_title,
                     normalized_location, job_description, crawl_timestamp.

    Modifies df IN PLACE (adds/updates columns) and returns it.
    """
    if "duplicate_flag" not in df.columns:
        df["duplicate_flag"] = False
    if "duplicate_group_id" not in df.columns:
        df["duplicate_group_id"] = None
    if "quality_flags" not in df.columns:
        df["quality_flags"] = [[] for _ in range(len(df))]

    # -----------------------------------------------------------------------
    # QR-05a: Exact duplicates (same source_url)
    # -----------------------------------------------------------------------
    url_seen: dict[str, str] = {}  # url → canonical job_id
    for i, row in df.iterrows():
        url = (row.get("source_url") or "").strip()
        if not url:
            continue
        if url in url_seen:
            df.at[i, "duplicate_flag"] = True
            df.at[i, "duplicate_group_id"] = url_seen[url]
            flags = list(df.at[i, "quality_flags"] or [])
            if "DUPLICATE_EXACT" not in flags:
                flags.append("DUPLICATE_EXACT")
            df.at[i, "quality_flags"] = flags
        else:
            url_seen[url] = row["job_id"]

    # -----------------------------------------------------------------------
    # QR-05b: Near duplicates
    # Only compare non-exact-duplicate records (canonical ones)
    # -----------------------------------------------------------------------
    # Build TF-IDF vectors for all JDs once
    jd_texts = list(df["job_description"].fillna(""))
    tfidf_vecs = _build_tfidf_vectors(jd_texts)

    n = len(df)
    indices = df.index.tolist()

    for a_pos in range(n):
        i = indices[a_pos]
        if df.at[i, "duplicate_flag"]:
            continue  # already flagged, skip

        comp_a = (df.at[i, "company"] or "").strip().lower()
        loc_a = df.at[i, "normalized_location"]
        title_a = df.at[i, "normalized_job_title"]

        for b_pos in range(a_pos + 1, n):
            j = indices[b_pos]
            if df.at[j, "duplicate_flag"]:
                continue  # already flagged, skip

            comp_b = (df.at[j, "company"] or "").strip().lower()

            # Must share company
            if comp_a != comp_b or not comp_a:
                continue

            jd_cos = _cosine(tfidf_vecs[a_pos], tfidf_vecs[b_pos])
            title_j = _jaccard(title_a, df.at[j, "normalized_job_title"])
            loc_b = df.at[j, "normalized_location"]

            is_near_dup = False
            dup_notes: list[str] = []

            # Standard path: title Jaccard ≥ 0.60 AND JD cosine ≥ 0.80 AND same location
            if (
                title_j >= NEAR_DUP_TITLE_JACCARD
                and jd_cos >= NEAR_DUP_JD_COSINE
                and loc_a == loc_b
            ):
                is_near_dup = True

            # High-confidence JD-only path (Leader proposal): JD cosine ≥ 0.95, same company
            elif jd_cos >= HIGH_CONF_JD_COSINE:
                is_near_dup = True
                dup_notes.append("HIGH_CONF_JD_ONLY")

            if is_near_dup:
                # Canonical = record with earlier index (a_pos)
                df.at[j, "duplicate_flag"] = True
                df.at[j, "duplicate_group_id"] = df.at[i, "job_id"]
                flags_j = list(df.at[j, "quality_flags"] or [])
                if "DUPLICATE_NEAR" not in flags_j:
                    flags_j.append("DUPLICATE_NEAR")
                if dup_notes:
                    flags_j.extend(dup_notes)
                if _has_seniority_diff(title_a, df.at[j, "normalized_job_title"]):
                    if "SENIORITY_VARIANT" not in flags_j:
                        flags_j.append("SENIORITY_VARIANT")
                df.at[j, "quality_flags"] = flags_j

    return df
