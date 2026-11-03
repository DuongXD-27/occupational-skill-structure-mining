"""
tests/cleaner/test_pipeline.py
End-to-end checks of run_pipeline: 22-field output, quality log, no deleted records.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pandas as pd
import pytest

from cleaner.pipeline import SCHEMA_FIELDS, QualityThresholdError, run_pipeline

_JD = ("Build data pipelines with Python, SQL and Apache Spark for the analytics team. "
       "Work with stakeholders on dashboards in Power BI.")
_JR = "3+ years with SQL, Python, Airflow. Good communication."


def _rec(i, **kw):
    rec = {f: None for f in SCHEMA_FIELDS}
    rec.update(
        job_id=f"J{i}", source="ITviec", source_url=f"https://itviec.com/it-jobs/j{i}",
        crawl_timestamp="2026-10-01T00:00:00+00:00", parser_version="v0.3",
        raw_job_title="Senior Data Engineer", company=f"Co{i}", raw_location="Ha Noi",
        job_description=_JD, job_requirements=_JR,
    )
    rec.update(kw)
    return rec


def _write(tmp_path, recs):
    p = tmp_path / "raw.jsonl"
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n", encoding="utf-8")
    return p


def test_output_has_exactly_22_fields_and_quality_log(tmp_path):
    raw = _write(tmp_path, [_rec(1), _rec(2, raw_experience="At office")])
    out = tmp_path / "clean.parquet"
    stats = run_pipeline(raw, out)
    df = pd.read_parquet(out)
    assert list(df.columns) == SCHEMA_FIELDS
    assert df["normalized_job_title"].tolist() == ["Data Engineer", "Data Engineer"]
    log = [json.loads(l) for l in Path(stats["quality_log"]).read_text(encoding="utf-8").splitlines()]
    assert [r["job_id"] for r in log] == ["J1", "J2"]
    assert "SCRAPER_FIELD_MISMATCH" in log[1]["quality_flags"]
    assert "SENIORITY_REMOVED" in log[0]["quality_flags"]


def test_raw_fields_unchanged(tmp_path):
    rec = _rec(1, raw_job_title="  Senior Data Engineer\n", raw_location=" Ha Noi ")
    out = tmp_path / "clean.jsonl"
    run_pipeline(_write(tmp_path, [rec]), out)
    row = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
    assert row["raw_job_title"] == "  Senior Data Engineer\n"
    assert row["raw_location"] == " Ha Noi "


def test_fatal_records_kept_and_flagged(tmp_path):
    recs = [_rec(i) for i in range(1, 10)] + [_rec(10, source_url="ftp://bad")]
    out = tmp_path / "clean.jsonl"
    stats = run_pipeline(_write(tmp_path, recs), out)
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 10
    bad = rows[-1]
    assert bad["relevance_flag"] is False and bad["exclusion_reason"] == "SCRAPE_ERROR"
    assert stats["scrape_error_job_ids"] == ["J10"]


def test_no_text_record_kept_as_insufficient_text(tmp_path):
    recs = [_rec(i) for i in range(1, 11)] + [_rec(11, job_description=None, job_requirements=None)]
    out = tmp_path / "clean.jsonl"
    run_pipeline(_write(tmp_path, recs), out)
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
    assert rows[-1]["relevance_flag"] is False
    assert rows[-1]["exclusion_reason"] == "INSUFFICIENT_TEXT"


def test_halts_when_too_many_records_lack_text(tmp_path):
    recs = [_rec(1), _rec(2, job_description=None, job_requirements=None)]
    with pytest.raises(QualityThresholdError):
        run_pipeline(_write(tmp_path, recs), tmp_path / "clean.parquet")


def test_location_mapping_override(tmp_path):
    mapping = tmp_path / "map.csv"
    mapping.write_text("raw_pattern,normalized_location\nha noi,Thủ đô\n", encoding="utf-8")
    out = tmp_path / "clean.parquet"
    run_pipeline(_write(tmp_path, [_rec(1)]), out, location_mapping_path=mapping)
    assert pd.read_parquet(out).loc[0, "normalized_location"] == "Thủ đô"
    # The default mapping is unaffected for later runs
    run_pipeline(_write(tmp_path, [_rec(1)]), out)
    assert pd.read_parquet(out).loc[0, "normalized_location"] != "Thủ đô"


def test_rejects_non_empty_legacy_columns(tmp_path):
    rec = _rec(1)
    rec["salary_raw"] = "Up to 2000 USD"
    with pytest.raises(ValueError, match="salary_raw"):
        run_pipeline(_write(tmp_path, [rec]), tmp_path / "clean.parquet")


def test_drops_empty_legacy_columns(tmp_path):
    rec = _rec(1)
    rec["experience_min_years"] = None
    out = tmp_path / "clean.parquet"
    run_pipeline(_write(tmp_path, [rec]), out)
    assert list(pd.read_parquet(out).columns) == SCHEMA_FIELDS
