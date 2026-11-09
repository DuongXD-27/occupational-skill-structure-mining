"""
src/cleaner/pipeline.py
Full cleaning pipeline — orchestrates QR-01 through QR-06 in order.

Execution order (report/main.tex §3.4):
  Step 1: Load raw data (read-only)
  Step 2: QR-01 — Missing value inspection (flag; fatal records are kept and
          excluded via relevance_flag=false, never deleted — scope §6, pipeline contract)
  Step 3: QR-05a — Exact duplicate check (source_url)
  Step 4: QR-02 — Normalize location
  Step 5: QR-03 — raw_experience is kept verbatim; only crawler field mismatches are
          flagged (no year parsing — decision 2026-10-04)
  Step 6: QR-04 — Normalize job title
  Step 7: QR-05b — Near-duplicate check (needs normalized_job_title + normalized_location)
  Step 8: QR-06 — Relevance classification
  Step 9: Export the 22-field table + a separate quality-flag log

Never modifies raw fields. All outputs go to derived (Stage B) fields.
The main table holds exactly the 22 schema fields (report/main.tex §3.3);
quality_flags are written to a JSONL log next to it (integration_decisions §D).
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional

import pandas as pd

from .location import load_mapping, normalize_location
from .title import normalize_title
from .relevance import classify_relevance
from .duplicates import detect_exact_duplicates, detect_near_duplicates

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Thresholds for dataset-wide warnings (QR-01 §2.3)
# ---------------------------------------------------------------------------
WARN_BOTH_TEXT_MISSING_PCT = 10.0
WARN_JR_MISSING_PCT = 20.0
WARN_LOCATION_MISSING_PCT = 30.0
WARN_DUPLICATE_PCT = 15.0

# The 22-field schema, in order (report/main.tex §3.3)
SCHEMA_FIELDS = (
    "job_id source source_job_id source_url crawl_timestamp parser_version raw_job_title "
    "normalized_job_title company raw_location normalized_location posted_date raw_experience "
    "job_description job_requirements job_text relevance_flag exclusion_reason "
    "duplicate_flag duplicate_group_id extracted_skills skill_count"
).split()

# Columns of older schema versions; dropped on input only when they hold no value.
LEGACY_FIELDS = (
    "experience_min_years", "experience_max_years", "education",
    "salary_raw", "salary_min", "salary_max", "salary_currency", "quality_flags",
)

# raw_experience values that are really work-mode/address strings (crawler selector bug)
_WORK_MODE_RE = re.compile(
    r"^\s*(at\s+office|hybrid|remote|onsite|on-site|work\s+from\s+home|wfh)\b",
    re.IGNORECASE,
)


class QualityThresholdError(RuntimeError):
    """QR-01 §2.3: too many records lack both text fields; the pipeline must stop."""


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

    Records with a fatal problem (missing title/source/URL, invalid URL) are kept
    in the audit table with relevance_flag=false and exclusion_reason=SCRAPE_ERROR;
    nothing is deleted. Returns (df, fatal_job_ids).

    Raises QualityThresholdError when more than WARN_BOTH_TEXT_MISSING_PCT % of the
    records miss both job_description and job_requirements (§2.3: halt the pipeline).
    """
    fatal_ids: list[str] = []

    for i, row in df.iterrows():
        flags = list(df.at[i, "quality_flags"] or [])
        fatal = None

        if not (row.get("raw_job_title") or "").strip():
            fatal = "MISSING_JOB_TITLE"
        elif not (row.get("source") or "").strip():
            fatal = "MISSING_SOURCE"
        else:
            url = (row.get("source_url") or "").strip()
            if not url:
                fatal = "MISSING_SOURCE_URL"
            elif not _validate_url(url):
                fatal = "INVALID_URL"

        if fatal:
            flags.append(fatal)
            df.at[i, "relevance_flag"] = False
            df.at[i, "exclusion_reason"] = "SCRAPE_ERROR"
            fatal_ids.append(row.get("job_id"))
            df.at[i, "quality_flags"] = flags
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

        df.at[i, "quality_flags"] = flags

    if fatal_ids:
        logger.warning("QR-01: %d records with fatal problems kept as SCRAPE_ERROR: %s",
                       len(fatal_ids), fatal_ids)

    # Dataset-wide checks
    n = len(df)
    if n == 0:
        return df, fatal_ids

    jd_empty = df["job_description"].fillna("").str.strip().eq("")
    jr_empty = df["job_requirements"].fillna("").str.strip().eq("")
    both_empty_pct = (jd_empty & jr_empty).sum() / n * 100
    jr_only_empty_pct = (jr_empty & ~jd_empty).sum() / n * 100
    loc_empty_pct = df["raw_location"].fillna("").str.strip().eq("").sum() / n * 100

    if both_empty_pct > WARN_BOTH_TEXT_MISSING_PCT:
        raise QualityThresholdError(
            f"QR-01: {both_empty_pct:.1f}% records missing both text fields "
            f"(threshold {WARN_BOTH_TEXT_MISSING_PCT}%). Halting pipeline!"
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

    return df, fatal_ids


def _experience_flags(raw: Optional[str]) -> list[str]:
    """QR-03: raw_experience is kept verbatim; flag crawler work-mode mismatches only."""
    if raw is None or not str(raw).strip():
        return []  # MISSING_EXPERIENCE already set by QR-01
    if _WORK_MODE_RE.search(str(raw)):
        return ["MISSING_EXPERIENCE", "SCRAPER_FIELD_MISMATCH"]
    return []


def _prepare_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Check input columns against the 22-field schema; drop empty legacy columns."""
    extra = [c for c in df.columns if c not in SCHEMA_FIELDS]
    blocking = []
    for col in extra:
        has_values = df[col].map(lambda v: v is not None and v == v and v != [] and v != "").any()
        if col in LEGACY_FIELDS and not has_values:
            logger.info("Dropping empty legacy column %s (old schema)", col)
        else:
            blocking.append(col)
    if blocking:
        raise ValueError(
            "Input has fields outside the 22-field schema: "
            + ", ".join(sorted(blocking))
            + ". Archive the old file and convert it before cleaning (integration_decisions §B)."
        )
    df = df.drop(columns=extra)
    for col in SCHEMA_FIELDS:
        if col not in df.columns:
            df[col] = None
    return df


# ---------------------------------------------------------------------------
# Main pipeline function
# ---------------------------------------------------------------------------



def run_pipeline(
    input_path: str | Path,
    output_path: str | Path,
    location_mapping_path: Optional[str | Path] = None,
    quality_log_path: Optional[str | Path] = None,
    allow_jd_only_duplicates: bool = False,
) -> dict:
    """
    Run the full cleaning pipeline.

    Parameters
    ----------
    input_path : path to raw .jsonl file (22-field schema)
    output_path : path to write the clean table (.parquet or .jsonl), exactly 22 fields
    location_mapping_path : optional alternative location_mapping.csv for this run
    quality_log_path : where to write per-record quality flags (JSONL);
        default ``<output_dir>/<output_stem>.quality_flags.jsonl``
    allow_jd_only_duplicates : enable the proposed JD-only near-duplicate path
        (not part of QR-05 yet; default off)

    Returns
    -------
    dict with pipeline statistics
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if quality_log_path is None:
        quality_log_path = output_path.with_name(output_path.stem + ".quality_flags.jsonl")
    quality_log_path = Path(quality_log_path)

    logger.info("Step 1: Loading raw data from %s", input_path)
    records = []
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    # dtype=object keeps None as None (pandas may otherwise infer StringDtype with NaN)
    df = _prepare_columns(pd.DataFrame(records, dtype=object))
    n_input = len(df)
    logger.info("Loaded %d records", n_input)

    df["quality_flags"] = [[] for _ in range(len(df))]
    df["duplicate_flag"] = False
    df["duplicate_group_id"] = None
    df["relevance_flag"] = None
    df["exclusion_reason"] = None
    df = df.astype({"relevance_flag": object, "exclusion_reason": object,
                    "duplicate_group_id": object, "normalized_job_title": object,
                    "normalized_location": object, "job_text": object})

    # Step 2: QR-01 — Missing value inspection
    logger.info("Step 2: QR-01 — Missing value inspection")
    df, fatal_ids = _apply_qr01(df)
    fatal = set(fatal_ids)

    # Step 3: QR-05a — Exact duplicates only (near duplicates need normalized fields)
    logger.info("Step 3: QR-05a — Exact duplicate check")
    detect_exact_duplicates(df)

    def _merge_flags(i, new_flags):
        flags = list(df.at[i, "quality_flags"] or [])
        flags.extend(f for f in new_flags if f not in flags)
        df.at[i, "quality_flags"] = flags

    # Step 4: QR-02 — Normalize location
    logger.info("Step 4: QR-02 — Normalizing location")
    location_rules = load_mapping(location_mapping_path) if location_mapping_path else None
    for i, row in df.iterrows():
        norm_loc, loc_flags = normalize_location(row.get("raw_location"), location_rules)
        df.at[i, "normalized_location"] = norm_loc
        _merge_flags(i, loc_flags)

    # Step 5: QR-03 — raw_experience kept verbatim; flag crawler mismatches
    logger.info("Step 5: QR-03 — Checking raw_experience (no year parsing)")
    for i, row in df.iterrows():
        _merge_flags(i, _experience_flags(row.get("raw_experience")))

    # Step 6: QR-04 — Normalize job title
    logger.info("Step 6: QR-04 — Normalizing job title")
    for i, row in df.iterrows():
        norm_title, title_flags = normalize_title(row.get("raw_job_title"))
        df.at[i, "normalized_job_title"] = norm_title
        _merge_flags(i, title_flags)

    # Step 7: QR-05b — Near-duplicate check (normalized fields are now available)
    logger.info("Step 7: QR-05b — Near-duplicate check")
    detect_near_duplicates(df, allow_jd_only=allow_jd_only_duplicates)

    n_duplicates = int(df["duplicate_flag"].sum())
    dup_pct = n_duplicates / len(df) * 100 if len(df) else 0
    if dup_pct > WARN_DUPLICATE_PCT:
        logger.warning("QR-05: %.1f%% records are duplicates (threshold %.0f%%)",
                       dup_pct, WARN_DUPLICATE_PCT)

    # Step 8: QR-06 — Relevance classification (fatal QR-01 records stay SCRAPE_ERROR)
    logger.info("Step 8: QR-06 — Classifying relevance")
    for i, row in df.iterrows():
        if row.get("job_id") in fatal:
            continue
        rel_flag, excl_reason, rel_flags = classify_relevance(
            normalized_job_title=row.get("normalized_job_title"),
            raw_job_title=row.get("raw_job_title"),
            job_description=row.get("job_description"),
            job_requirements=row.get("job_requirements"),
        )
        df.at[i, "relevance_flag"] = bool(rel_flag)
        df.at[i, "exclusion_reason"] = excl_reason
        _merge_flags(i, rel_flags)

    # job_text: description + requirements for skill extraction (schema §4)
    def _make_job_text(row) -> Optional[str]:
        jd = (row.get("job_description") or "").strip()
        jr = (row.get("job_requirements") or "").strip()
        if jd and jr:
            return jd + "\n\n" + jr
        return jd or jr or None

    df["job_text"] = df.apply(_make_job_text, axis=1)

    # Step 9: Export — main table (22 fields) + quality-flag log
    logger.info("Step 9: Exporting to %s", output_path)
    df["relevance_flag"] = df["relevance_flag"].astype(bool)
    df["duplicate_flag"] = df["duplicate_flag"].astype(bool)
    quality = df[["job_id", "quality_flags"]].copy()
    out = df[SCHEMA_FIELDS].copy()

    if output_path.suffix.lower() == ".jsonl":
        with open(output_path, "w", encoding="utf-8", newline="\n") as f:
            for rec in out.to_dict(orient="records"):
                rec = {k: (None if isinstance(v, float) and v != v else v) for k, v in rec.items()}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    else:
        out.to_parquet(output_path, index=False, engine="pyarrow")

    quality_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(quality_log_path, "w", encoding="utf-8", newline="\n") as f:
        for rec in quality.to_dict(orient="records"):
            f.write(json.dumps({"job_id": rec["job_id"], "quality_flags": list(rec["quality_flags"])},
                               ensure_ascii=False) + "\n")
    logger.info("Exported %d records; quality log %s", len(out), quality_log_path)

    # Stats
    rel = df["relevance_flag"]
    dup = df["duplicate_flag"]
    stats = {
        "n_input": n_input,
        "n_output": len(out),
        "n_scrape_error": len(fatal_ids),
        "n_duplicates": n_duplicates,
        "n_out_of_scope": int((~rel).sum()),
        "n_out_of_scope_and_duplicate": int((~rel & dup).sum()),
        "n_valid": int((rel & ~dup).sum()),
        "unique_raw_titles": int(df["raw_job_title"].map(lambda t: " ".join(str(t).split()).lower()).nunique()),
        "unique_normalized_titles": int(df["normalized_job_title"].dropna().nunique()),
        "unique_normalized_locations": int(df["normalized_location"].dropna().nunique()),
        "scrape_error_job_ids": fatal_ids,
        "quality_log": str(quality_log_path),
    }
    logger.info("Pipeline complete. Stats: %s", stats)
    return stats
