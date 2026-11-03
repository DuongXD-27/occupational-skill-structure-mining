"""tests/cleaner/test_rq1.py — RQ1 metrics."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pandas as pd
import pytest

from cleaner.rq1 import ARTIFACTS, compute_rq1, raw_title_key, write_rq1


def _df():
    rows = [
        ("Senior Data Analyst", "Data Analyst", "A", True, False),
        ("DATA ANALYST", "Data Analyst", "B", True, False),
        ("Data  Analyst", "Data Analyst", "C", True, False),
        ("Data Engineer", "Data Engineer", "A", True, False),
        ("Prompt Wizard", "Prompt Wizard", "Z", True, False),
        ("Data Analyst", "Data Analyst", "D", True, True),     # duplicate → excluded
        ("Sales Manager", "Sales Manager", "E", False, False),  # out of scope → excluded
    ]
    return pd.DataFrame(
        [{"raw_job_title": r, "normalized_job_title": n, "company": c, "relevance_flag": rel,
          "duplicate_flag": dup, "source_url": f"https://x/{i}"} for i, (r, n, c, rel, dup) in enumerate(rows)]
    )


def test_raw_key_is_trim_lower():
    assert raw_title_key("  Data  Analyst\n") == "data analyst"


def test_metrics():
    res = compute_rq1(_df())
    m = dict(zip(res["summary"]["metric"], res["summary"]["value"]))
    assert m["n_postings"] == 5
    assert m["n_raw_titles"] == 4          # senior data analyst, data analyst, data engineer, prompt wizard
    assert m["n_normalized_titles"] == 3
    assert m["compression_ratio"] == pytest.approx(0.75)
    assert m["top1_share"] == pytest.approx(0.6)
    assert m["n_rare_titles"] == 2
    assert m["sample_note"] == "pipeline_test"
    assert set(res["rare"]["normalized_job_title"]) == {"Data Engineer", "Prompt Wizard"}


def test_write_creates_artifacts(tmp_path):
    clean = tmp_path / "clean.parquet"
    _df().to_parquet(clean, index=False)
    status = write_rq1(clean, tmp_path / "rq1")
    assert status["RQ1"]["status"] == "completed"
    for name in ARTIFACTS:
        assert (tmp_path / "rq1" / name).stat().st_size > 0
