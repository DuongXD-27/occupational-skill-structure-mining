import json
from pathlib import Path
from types import SimpleNamespace

import pyarrow.parquet as pq
import pytest

from src.parser.features import export_features, run
from src.parser.skill_extractor import DEFAULT_TAXONOMY


def jobs(tmp_path, mutation=None):
    rows = [dict(job_id="j1", raw_job_title="Data Engineer", job_description="Python and Power BI", job_requirements=None,
                 relevance_flag=True, duplicate_flag=False),
            dict(job_id="j2", job_description="SQL", relevance_flag=True, duplicate_flag=True),
            dict(job_id="j3", job_description="SQL", relevance_flag=False, duplicate_flag=False),
            dict(job_id="j4", job_description="Welcome to the team", relevance_flag=True, duplicate_flag=False)]
    if mutation:
        mutation(rows)
    path = tmp_path / "clean.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


def test_artifacts_filter_ids_and_align_matrix(tmp_path):
    clean = jobs(tmp_path)
    before = clean.read_bytes()
    skills, matrix = tmp_path / "skills.parquet", tmp_path / "matrix.parquet"
    context = SimpleNamespace(paths=dict(clean=clean, skills=skills, matrix=matrix, taxonomy=DEFAULT_TAXONOMY), options={})
    report = run(context)
    rows = pq.read_table(skills).to_pylist()
    assert rows == [dict(job_id="j1", extracted_skills=["Power BI", "Python"], skill_count=2),
                    dict(job_id="j4", extracted_skills=[], skill_count=0)]
    from src.parser import SkillExtractor
    names = {r["canonical_name"]: r["skill_id"] for r in SkillExtractor().rows}
    values = pq.read_table(matrix).to_pylist()
    assert [r["job_id"] for r in values] == ["j1", "j4"]
    assert values[0][names["Python"]] == values[0][names["Power BI"]] == 1
    assert sum(v for k, v in values[0].items() if k != "job_id") == 2
    assert sum(v for k, v in values[1].items() if k != "job_id") == 0
    assert report["feature_records"] == 2
    assert clean.read_bytes() == before


@pytest.mark.parametrize("mutation", [
    lambda r: r[0].update(relevance_flag="true"),
    lambda r: r[0].update(duplicate_flag=None),
    lambda r: r[0].pop("relevance_flag"),
    lambda r: r[1].update(job_id="j1"),
    lambda r: r[0].update(job_description=123),
    lambda r: [x.update(relevance_flag=False) for x in r],
    lambda r: r[0].update(job_description=None, job_requirements=None),
])
def test_invalid_input_preserves_outputs(tmp_path, mutation):
    clean = jobs(tmp_path, mutation)
    output = tmp_path / "skills.parquet"
    output.write_bytes(b"previous artifact")
    with pytest.raises(ValueError):
        export_features(clean, output, tmp_path / "matrix.parquet")
    assert output.read_bytes() == b"previous artifact"


def test_paths_cannot_overwrite_inputs(tmp_path):
    clean = jobs(tmp_path)
    with pytest.raises(ValueError, match="ghi đè"):
        export_features(clean, clean, tmp_path / "matrix.parquet")
    with pytest.raises(ValueError, match="trùng"):
        export_features(clean, tmp_path / "same.parquet", tmp_path / "same.parquet")


def test_pipeline_cannot_enable_raw_preview(tmp_path):
    with pytest.raises(ValueError, match="dữ liệu sạch"):
        run(SimpleNamespace(paths={}, options={"preview": True}))


def test_raw_preview_is_explicit(tmp_path):
    clean = jobs(tmp_path, lambda r: [x.pop("relevance_flag") for x in r])
    report = export_features(clean, tmp_path / "skills.parquet", tmp_path / "matrix.parquet", preview=True)
    assert report["artifact_kind"] == "raw_preview" and report["feature_records"] == 4


def test_clean_parquet_input(tmp_path):
    import pyarrow as pa
    raw = jobs(tmp_path)
    rows = [json.loads(line) for line in raw.read_text().splitlines()]
    clean = tmp_path / "clean.parquet"
    pq.write_table(pa.Table.from_pylist(rows), clean)
    report = export_features(clean, tmp_path / "skills.parquet", tmp_path / "matrix.parquet")
    assert report["feature_records"] == 2
