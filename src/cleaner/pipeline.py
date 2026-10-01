"""
src/cleaner/pipeline.py
Full cleaning pipeline — orchestrates QR-01 through QR-06 in order.

Execution order (from docs/data_cleaning/data_quality_rules.md §8):
  Step 1: Load raw data (read-only)
  Step 2: QR-01 — Missing value inspection (drop fatal records, flag others)
  Step 3: QR-05a — Exact duplicate check (source_url)
  Step 4: QR-02 — Normalize location
  Step 5: QR-03 — Normalize experience
  Step 6: QR-04 — Normalize job title
  Step 7: QR-05b — Near-duplicate check (needs normalized_job_title + normalized_location)
  Step 8: QR-06 — Relevance classification
  Step 9: Export to parquet

Never modifies raw fields. All outputs go to derived (Stage B) fields.
"""

from __future__ import annotations

import json
import logging
import re
import warnings
from pathlib import Path
from typing import Optional

import pandas as pd

from .location import normalize_location
from .experience import parse_experience
from .title import normalize_title
from .relevance import classify_relevance
from .duplicates import detect_duplicates

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Thresholds for dataset-wide warnings (QR-01 §2.3)
# ---------------------------------------------------------------------------
WARN_BOTH_TEXT_MISSING_PCT = 10.0
WARN_JR_MISSING_PCT = 20.0
WARN_LOCATION_MISSING_PCT = 30.0
WARN_DUPLICATE_PCT = 15.0


# ---------------------------------------------------------------------------
# QR-01: Missing value handling
# ---------------------------------------------------------------------------

def _validate_url(url: Optional[str]) -> bool:
    """Basic URL validity check (starts with http)."""
    if not url:
        return False
    return bool(url.strip().startswith("http"))


def _apply_qr01(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Apply QR-01 missing value rules.
    Returns (cleaned_df, dropped_job_ids).
    """
    drop_mask = pd.Series(False, index=df.index)
    quality_flags: dict[int, list[str]] = {i: [] for i in df.index}

    for i, row in df.iterrows():
        flags = quality_flags[i]

        # Fatal: missing raw_job_title
        if not (row.get("raw_job_title") or "").strip():
            drop_mask[i] = True
            flags.append("MISSING_JOB_TITLE")
            continue

        # Fatal: missing source
        if not (row.get("source") or "").strip():
            drop_mask[i] = True
            flags.append("MISSING_SOURCE")
            continue

        # Fatal: missing / invalid source_url
        url = (row.get("source_url") or "").strip()
        if not url:
            drop_mask[i] = True
            flags.append("MISSING_SOURCE_URL")
            continue
        if not _validate_url(url):
            drop_mask[i] = True
            flags.append("INVALID_URL")
            continue

        # Non-fatal flags
        if not (row.get("crawl_timestamp") or ""):
            flags.append("MISSING_CRAWL_TIMESTAMP")
        if not (row.get("company") or "").strip():
            flags.append("MISSING_COMPANY")
        if not (row.get("raw_location") or "").strip():
            flags.append("MISSING_LOCATION")
        if not (row.get("raw_experience") or "").strip():
            flags.append("MISSING_EXPERIENCE")
        if not (row.get("parser_version") or "").strip():
            flags.append("MISSING_PARSER_VERSION")

        # Text fields
        jd = (row.get("job_description") or "").strip()
        jr = (row.get("job_requirements") or "").strip()

        if not jd:
            flags.append("MISSING_JOB_DESCRIPTION")
        if not jr:
            flags.append("MISSING_JOB_REQUIREMENTS")

        # Scrape error check (§2.4) — only when text exists but too short
        if jd and jr and len(jd) < 30 and len(jr) < 30:
            flags.append("SCRAPE_FAILED")

        # HTML / error title (§2.4)
        title = (row.get("raw_job_title") or "")
        if re.search(r"<[^>]+>|404|page\s+not\s+found", title, re.IGNORECASE):
            flags.append("SCRAPE_ERROR_CONTENT")

    dropped_ids = list(df.loc[drop_mask, "job_id"])
    if dropped_ids:
        logger.warning("QR-01 dropped %d records: %s", len(dropped_ids), dropped_ids)

    df = df.loc[~drop_mask].copy()
    # Merge flags into existing quality_flags column
    for i in df.index:
        existing = list(df.at[i, "quality_flags"] or [])
        existing.extend(quality_flags.get(i, []))
        df.at[i, "quality_flags"] = existing

    # Dataset-wide warnings
    n = len(df)
    if n == 0:
        return df, dropped_ids

    jd_empty = df["job_description"].fillna("").str.strip().eq("")
    jr_empty = df["job_requirements"].fillna("").str.strip().eq("")
    both_empty_pct = (jd_empty & jr_empty).sum() / n * 100
    jr_only_empty_pct = (jr_empty & ~jd_empty).sum() / n * 100
    loc_empty_pct = df["raw_location"].fillna("").str.strip().eq("").sum() / n * 100

    if both_empty_pct > WARN_BOTH_TEXT_MISSING_PCT:
        warnings.warn(
            f"QR-01: {both_empty_pct:.1f}% records missing both text fields "
            f"(threshold {WARN_BOTH_TEXT_MISSING_PCT}%). Halting pipeline!",
            RuntimeWarning,
            stacklevel=2,
        )
    if jr_only_empty_pct > WARN_JR_MISSING_PCT:
        logger.warning(
            "QR-01: %.1f%% records missing job_requirements (threshold %.0f%%)",
            jr_only_empty_pct, WARN_JR_MISSING_PCT,
        )
    if loc_empty_pct > WARN_LOCATION_MISSING_PCT:
        logger.warning(
            "QR-01: %.1f%% records missing raw_location (threshold %.0f%%)",
            loc_empty_pct, WARN_LOCATION_MISSING_PCT,
        )

    return df, dropped_ids


# ---------------------------------------------------------------------------
# Main pipeline function
# ---------------------------------------------------------------------------



def run_pipeline(
    input_path: str | Path,
    output_path: str | Path,
    location_mapping_path: Optional[str | Path] = None,
) -> dict:
    """
    Run the full cleaning pipeline.

    Parameters
    ----------
    input_path : path to raw .jsonl file
    output_path : path to write jobs_clean.parquet
    location_mapping_path : optional override for location_mapping.csv path

    Returns
    -------
    dict with pipeline statistics
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Step 1: Loading raw data from %s", input_path)
    records = []
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    df = pd.DataFrame(records)
    n_input = len(df)
    logger.info("Loaded %d records", n_input)

    # Ensure all Stage B columns exist (set to None / empty list)
    stage_b_cols = [
        "normalized_job_title", "normalized_location",
        "experience_min_years", "experience_max_years",
        "relevance_flag", "exclusion_reason",
        "duplicate_flag", "duplicate_group_id",
        "quality_flags", "job_text",
    ]
    for col in stage_b_cols:
        if col not in df.columns:
            if col == "quality_flags":
                df[col] = [[] for _ in range(len(df))]
            elif col in ("duplicate_flag", "relevance_flag"):
                df[col] = None
            else:
                df[col] = None
        elif col == "quality_flags":
            df[col] = df[col].apply(lambda x: list(x) if isinstance(x, list) else [])

    # -----------------------------------------------------------------------
    # Step 2: QR-01 — Missing value inspection
    # -----------------------------------------------------------------------
    logger.info("Step 2: QR-01 — Missing value inspection")
    df, dropped_ids = _apply_qr01(df)
    n_after_qr01 = len(df)

    # -----------------------------------------------------------------------
    # Step 3: QR-05a — Exact duplicate check (source_url)
    # -----------------------------------------------------------------------
    logger.info("Step 3: QR-05a — Exact duplicate check")
    df = detect_duplicates(df)  # runs both 05a and (later) 05b; 05b needs title first

    # Reset: we'll run 05b properly after title normalization (Step 7).
    # For now, exact duplicates are already marked. Near-dup will be re-run in Step 7.
    # (detect_duplicates is idempotent w.r.t. already-flagged records.)

    # -----------------------------------------------------------------------
    # Step 4: QR-02 — Normalize location
    # -----------------------------------------------------------------------
    logger.info("Step 4: QR-02 — Normalizing location")
    for i, row in df.iterrows():
        norm_loc, loc_flags = normalize_location(row.get("raw_location"))
        df.at[i, "normalized_location"] = norm_loc
        flags = list(df.at[i, "quality_flags"] or [])
        flags.extend(f for f in loc_flags if f not in flags)
        df.at[i, "quality_flags"] = flags

    # -----------------------------------------------------------------------
    # Step 5: QR-03 — Normalize experience
    # -----------------------------------------------------------------------
    logger.info("Step 5: QR-03 — Normalizing experience")
    for i, row in df.iterrows():
        min_y, max_y, exp_flags = parse_experience(row.get("raw_experience"))
        df.at[i, "experience_min_years"] = min_y
        df.at[i, "experience_max_years"] = max_y
        flags = list(df.at[i, "quality_flags"] or [])
        flags.extend(f for f in exp_flags if f not in flags)
        df.at[i, "quality_flags"] = flags

    # -----------------------------------------------------------------------
    # Step 6: QR-04 — Normalize job title
    # -----------------------------------------------------------------------
    logger.info("Step 6: QR-04 — Normalizing job title")
    for i, row in df.iterrows():
        norm_title, title_flags = normalize_title(row.get("raw_job_title"))
        df.at[i, "normalized_job_title"] = norm_title
        flags = list(df.at[i, "quality_flags"] or [])
        flags.extend(f for f in title_flags if f not in flags)
        df.at[i, "quality_flags"] = flags

    # -----------------------------------------------------------------------
    # Step 7: QR-05b — Near-duplicate check
    # (now that normalized_job_title and normalized_location are available)
    # -----------------------------------------------------------------------
    logger.info("Step 7: QR-05b — Near-duplicate check")
    df = detect_duplicates(df)

    n_duplicates = int(df["duplicate_flag"].fillna(False).sum())
    dup_pct = n_duplicates / len(df) * 100 if len(df) else 0
    if dup_pct > WARN_DUPLICATE_PCT:
        logger.warning(
            "QR-05: %.1f%% records are duplicates (threshold %.0f%%)",
            dup_pct, WARN_DUPLICATE_PCT,
        )

    # -----------------------------------------------------------------------
    # Step 8: QR-06 — Relevance classification
    # -----------------------------------------------------------------------
    logger.info("Step 8: QR-06 — Classifying relevance")
    for i, row in df.iterrows():
        rel_flag, excl_reason, rel_flags = classify_relevance(
            normalized_job_title=row.get("normalized_job_title"),
            raw_job_title=row.get("raw_job_title"),
            job_description=row.get("job_description"),
            job_requirements=row.get("job_requirements"),
        )
        df.at[i, "relevance_flag"] = rel_flag
        df.at[i, "exclusion_reason"] = excl_reason
        flags = list(df.at[i, "quality_flags"] or [])
        flags.extend(f for f in rel_flags if f not in flags)
        df.at[i, "quality_flags"] = flags

    # -----------------------------------------------------------------------
    # Build job_text (concat for skill extraction — not part of Deliverable 1 rules,
    # but schema §4 includes this field and Cường depends on it)
    # -----------------------------------------------------------------------
    def _make_job_text(row) -> Optional[str]:
        jd = (row.get("job_description") or "").strip()
        jr = (row.get("job_requirements") or "").strip()
        if jd and jr:
            return jd + "\n\n" + jr
        return jd or jr or None

    df["job_text"] = df.apply(_make_job_text, axis=1)

    # -----------------------------------------------------------------------
    # Step 9: Export
    # -----------------------------------------------------------------------
    logger.info("Step 9: Exporting to %s", output_path)

    # Convert quality_flags list to JSON string for parquet compatibility
    df["quality_flags"] = df["quality_flags"].apply(
        lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, list) else "[]"
    )

    df.to_parquet(output_path, index=False, engine="pyarrow")
    logger.info("Exported %d records", len(df))

    # -----------------------------------------------------------------------
    # Build and return stats
    # -----------------------------------------------------------------------
    n_final = len(df)
    n_irrelevant = int((df["relevance_flag"] == False).sum())  # noqa: E712
    n_relevant = int((df["relevance_flag"] == True).sum())  # noqa: E712

    unique_raw_titles = df["raw_job_title"].nunique()
    unique_norm_titles = df["normalized_job_title"].dropna().nunique()
    unique_norm_locs = df["normalized_location"].dropna().nunique()

    stats = {
        "n_input": n_input,
        "n_dropped_qr01": n_input - n_after_qr01,
        "n_after_qr01": n_after_qr01,
        "n_duplicates": n_duplicates,
        "n_out_of_scope": n_irrelevant,
        "n_final": n_final,
        "unique_raw_titles": unique_raw_titles,
        "unique_normalized_titles": unique_norm_titles,
        "unique_normalized_locations": unique_norm_locs,
        "dropped_job_ids": dropped_ids,
    }
    logger.info("Pipeline complete. Stats: %s", stats)
    return stats
