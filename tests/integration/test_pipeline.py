"""Kiểm thử các ranh giới bàn giao; module giả lập chỉ chép fixture có sẵn."""

import json
from datetime import date, datetime
from pathlib import Path
import shutil
import subprocess
import sys
import types

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.pipeline.config import PipelineError, load_config
from src.pipeline.contracts import FIELDS
from src.pipeline.runner import run_pipeline


def jsonl(path, rows):
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def parquet(path, rows):
    pq.write_table(pa.Table.from_pylist(rows), path)


def write_table(path, rows):
    if path.suffix == ".jsonl":
        jsonl(path, rows)
    else:
        parquet(path, rows)


@pytest.fixture
def project(tmp_path, monkeypatch):
    raw = []
    titles = ["Senior Data Analyst", "Data Analyst", "DATA ANALYST", "Sales AI"]
    for i, title in enumerate(titles, 1):
        row = dict.fromkeys(FIELDS)
        row.update(job_id=f"j{i}", source="ITviec", source_url=f"https://example.org/jobs/{i}",
                   crawl_timestamp="2026-10-03T00:00:00+00:00", parser_version="fixture",
                   raw_job_title=title, job_description="SQL", job_requirements="Python")
        raw.append(row)
    clean = []
    for i, row in enumerate(raw):
        clean.append({**row, "normalized_job_title": "Data Analyst" if i < 3 else "Sales AI",
                      "job_text": "SQL\nPython", "relevance_flag": i != 3,
                      "duplicate_flag": i == 2,
                      "exclusion_reason": "OUT_OF_SCOPE" if i == 3 else None})
    skills = [{"job_id": f"j{i}", "extracted_skills": ["SQL", "Python"], "skill_count": 2}
              for i in (1, 2)]
    matrix = [{"job_id": f"j{i}", "SK1": 1, "SK2": 1} for i in (1, 2)]
    jsonl(tmp_path / "raw.jsonl", raw)
    jsonl(tmp_path / "clean_fixture.jsonl", clean)
    jsonl(tmp_path / "skills_fixture.jsonl", skills)
    jsonl(tmp_path / "matrix_fixture.jsonl", matrix)
    (tmp_path / "taxonomy.csv").write_text("skill_id,canonical_name\nSK1,SQL\nSK2,Python\n", encoding="utf-8")
    config = {
        "version": 1, "run_kind": "integration",
        "paths": {"raw": "raw.jsonl", "clean": "clean.parquet", "skills": "skills.parquet",
                  "matrix": "matrix.parquet", "taxonomy": "taxonomy.csv", "rq1": "rq1",
                  "analysis": "analysis", "report": "run.json"},
        "modules": {s: f"fixture_modules:{s}" for s in ("clean", "rq1", "extract", "analysis")},
        "options": {},
    }
    config_path = tmp_path / "pipeline.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    calls = []
    module = types.ModuleType("fixture_modules")

    def fixture_rows(name):
        return [json.loads(line) for line in (tmp_path / name).read_text(encoding="utf-8").splitlines()]

    def clean_module(ctx):
        calls.append(ctx.stage)
        write_table(ctx.paths["clean"], fixture_rows("clean_fixture.jsonl"))

    def extract_module(ctx):
        calls.append(ctx.stage)
        write_table(ctx.paths["skills"], fixture_rows("skills_fixture.jsonl"))
        write_table(ctx.paths["matrix"], fixture_rows("matrix_fixture.jsonl"))

    def rq_module(ctx):
        calls.append(ctx.stage)
        (ctx.paths[ctx.stage] / "fixture.csv").write_text("fixture,value\nmodule_contract,1\n", encoding="utf-8")
        questions = ("RQ1",) if ctx.stage == "rq1" else ("RQ2", "RQ3", "RQ4")
        return {rq: {"status": "completed", "artifacts": ["fixture.csv"]} for rq in questions}

    module.clean, module.extract, module.rq1, module.analysis = clean_module, extract_module, rq_module, rq_module
    monkeypatch.setitem(sys.modules, "fixture_modules", module)
    return types.SimpleNamespace(root=tmp_path, config=config, path=config_path, calls=calls,
                                 raw=raw, clean=clean, skills=skills, matrix=matrix, module=module)


def save_config(project):
    project.path.write_text(json.dumps(project.config), encoding="utf-8")


def test_full_chain_and_counts(project):
    before = (project.root / "raw.jsonl").read_bytes()
    report = run_pipeline(project.path)
    assert project.calls == ["clean", "rq1", "extract", "analysis"]
    assert report["counts"] == {"raw_records": 4, "clean_records": 4, "valid_records": 2,
                                "duplicates": 1, "out_of_scope": 1, "overlap": 0,
                                "skill_records": 2, "matrix_rows": 2}
    assert (project.root / "raw.jsonl").read_bytes() == before
    assert report["status"] == "completed" and report["research_acceptance"] is False
    assert report["rq"]["RQ1"]["owner"] == "Đức"
    assert all(item["status"] == "completed" for item in report["rq"].values())
    assert json.loads((project.root / "run.json").read_text(encoding="utf-8")) == report
    assert (project.root / "analysis" / "manifest.json").is_file()
    assert report["stages"]["extract"]["inputs"]["clean"]["sha256"]


def test_rerun_extract_without_raw_or_rq1(project):
    run_pipeline(project.path, "clean")
    (project.root / "raw.jsonl").unlink()
    project.calls.clear()
    first = run_pipeline(project.path, "extract")
    second = run_pipeline(project.path, "extract")
    assert project.calls == ["extract", "extract"]
    assert first["counts"] == second["counts"]
    assert second["rq"]["RQ1"]["status"] == "not_run"
    project.calls.clear()
    assert run_pipeline(project.path, "analysis")["status"] == "completed"
    assert project.calls == ["analysis"]


def test_missing_field_stops_before_extractor(project):
    rows = [{k: v for k, v in r.items() if k != "relevance_flag"} for r in project.clean]
    parquet(project.root / "clean.parquet", rows)
    with pytest.raises(PipelineError, match="thiếu trường relevance_flag"):
        run_pipeline(project.path, "extract")
    assert project.calls == []
    report = json.loads((project.root / "run.json").read_text(encoding="utf-8"))
    assert report["stages"]["extract"]["status"] == "failed"


@pytest.mark.parametrize("mutation,expected", [
    (lambda rows: rows[0].update(relevance_flag="true"), "relevance_flag"),
    (lambda rows: rows[0].update(duplicate_flag=None), "duplicate_flag"),
    (lambda rows: rows[0].update(raw_job_title="Changed"), "ghi đè trường gốc"),
    (lambda rows: rows[0].update(job_id="changed"), "mất/thêm job_id"),
    (lambda rows: rows[1].update(job_id="j1"), "job_id bị lặp"),
    (lambda rows: rows[3].update(exclusion_reason=None), "exclusion_reason"),
    (lambda rows: [r.update(quality_flags=[]) for r in rows], "ngoài schema 22"),
])
def test_cleaner_contract_failures(project, mutation, expected):
    # JSONL cho phép kiểm tra kiểu hỗn hợp mà writer Parquet đã chặn trước đó.
    project.config["paths"]["clean"] = "clean.jsonl"
    save_config(project)
    mutation(project.clean)
    jsonl(project.root / "clean_fixture.jsonl", project.clean)
    with pytest.raises(PipelineError, match=expected):
        run_pipeline(project.path)
    assert project.calls == ["clean"]
    assert not (project.root / "clean.jsonl").exists()


@pytest.mark.parametrize("mutation,expected", [
    (lambda p: p.skills[0].update(skill_count=1), "skill_count"),
    (lambda p: p.skills[0].update(extracted_skills="SQL"), "list\\[string\\]"),
    (lambda p: p.skills[0].update(extracted_skills=["Unknown", "Python"]), "ngoài taxonomy"),
    (lambda p: p.skills[0].update(extracted_skills=["SQL", "SQL"]), "kỹ năng trùng"),
    (lambda p: p.matrix[0].update(SK1=2), "số nguyên 0/1"),
    (lambda p: p.matrix[0].update(SK1=0), "ma trận không khớp"),
    (lambda p: p.skills.append({"job_id": "j3", "extracted_skills": [], "skill_count": 0}), "job_id phải khớp"),
])
def test_features_contract_failures(project, mutation, expected):
    project.config["paths"]["skills"] = "skills.jsonl"
    save_config(project)
    run_pipeline(project.path, "clean")
    mutation(project)
    jsonl(project.root / "skills_fixture.jsonl", project.skills)
    jsonl(project.root / "matrix_fixture.jsonl", project.matrix)
    with pytest.raises(PipelineError, match=expected):
        run_pipeline(project.path, "extract")
    assert not (project.root / "skills.jsonl").exists()


def test_no_output_cannot_reuse_stale_file(project):
    run_pipeline(project.path, "clean")
    previous = (project.root / "clean.parquet").read_bytes()
    project.module.clean = lambda ctx: None
    with pytest.raises(PipelineError, match="không tìm thấy file"):
        run_pipeline(project.path, "clean")
    assert (project.root / "clean.parquet").read_bytes() == previous


def test_failed_extraction_preserves_old_features(project):
    run_pipeline(project.path)
    before = {name: (project.root / name).read_bytes() for name in ("skills.parquet", "matrix.parquet")}
    project.matrix[0]["SK1"] = 2
    jsonl(project.root / "matrix_fixture.jsonl", project.matrix)
    with pytest.raises(PipelineError):
        run_pipeline(project.path, "extract")
    assert all((project.root / name).read_bytes() == value for name, value in before.items())


def test_missing_module_is_explicit(project):
    project.config["modules"]["rq1"] = None
    save_config(project)
    with pytest.raises(PipelineError, match="Chưa bàn giao module rq1"):
        run_pipeline(project.path)
    report = json.loads((project.root / "run.json").read_text(encoding="utf-8"))
    assert report["rq"]["RQ1"]["status"] == "failed"
    assert report["stages"]["extract"]["status"] == "not_run"


def test_module_exception_is_reported(project):
    def broken(ctx):
        raise RuntimeError("parser failed")
    project.module.clean = broken
    with pytest.raises(PipelineError, match="parser failed"):
        run_pipeline(project.path)
    assert json.loads((project.root / "run.json").read_text(encoding="utf-8"))["status"] == "failed"


def test_readonly_input_mutation_is_detected(project):
    def broken(ctx):
        ctx.paths["raw"].write_text("changed", encoding="utf-8")
    project.module.clean = broken
    with pytest.raises(PipelineError, match="đã sửa đầu vào chỉ đọc"):
        run_pipeline(project.path, "clean")


@pytest.mark.parametrize("result,expected", [
    ({"RQ1": {"status": "completed", "artifacts": []}}, "phải có file kết quả"),
    ({"RQ1": {"status": "skipped"}}, "phải có reason"),
    ({"RQ1": {"status": "completed", "artifacts": ["../outside.csv"]}}, "nằm ngoài thư mục"),
    ({"RQ1": {"status": "completed", "artifacts": ["missing.csv"]}}, "không tồn tại"),
    ({"RQ2": {"status": "completed"}}, "trả đúng trạng thái"),
])
def test_rq_handoff_contract(project, result, expected):
    run_pipeline(project.path, "clean")
    project.module.rq1 = lambda ctx: result
    with pytest.raises(PipelineError, match=expected):
        run_pipeline(project.path, "rq1")


def test_skipped_rq_is_not_research_acceptance(project):
    project.config["run_kind"] = "research"
    save_config(project)
    original = project.module.analysis
    def small_sample(ctx):
        result = original(ctx)
        result["RQ4"] = {"status": "skipped", "reason": "Chưa đạt 300 tin.", "artifacts": []}
        return result
    project.module.analysis = small_sample
    report = run_pipeline(project.path)
    assert report["status"] == "completed"
    assert report["research_acceptance"] is False
    assert report["rq"]["RQ4"]["status"] == "skipped"


def test_overlapping_rejection_counts(project):
    project.clean[2].update(relevance_flag=False, exclusion_reason="OUT_OF_SCOPE")
    jsonl(project.root / "clean_fixture.jsonl", project.clean)
    counts = run_pipeline(project.path, "clean")["counts"]
    assert counts["valid_records"] == 2
    assert counts["clean_records"] == counts["valid_records"] + counts["duplicates"] + counts["out_of_scope"] - counts["overlap"]


def test_config_paths_are_relative_to_config_not_cwd(project, monkeypatch):
    other = project.root / "other"
    other.mkdir()
    monkeypatch.chdir(other)
    assert load_config(project.path).paths["raw"] == project.root / "raw.jsonl"
    assert run_pipeline(project.path, "clean")["status"] == "completed"


@pytest.mark.parametrize("target", ["raw.jsonl", "rq1/nested.jsonl"])
def test_config_disallows_overwriting_inputs_or_nested_outputs(project, target):
    project.config["paths"]["skills"] = target
    save_config(project)
    with pytest.raises(PipelineError, match="trùng/lồng nhau"):
        load_config(project.path)


def test_existing_cleaner_adapter_forwards_only_paths_and_options(project, monkeypatch):
    cleaner_package = types.ModuleType("src.cleaner")
    cleaner_module = types.ModuleType("src.cleaner.pipeline")
    forwarded = {}
    def run_cleaner(input_path, output_path, **kwargs):
        forwarded.update(input_path=input_path, options=kwargs)
        shutil.copyfile(project.root / "clean_fixture.jsonl", output_path)
    cleaner_module.run_pipeline = run_cleaner
    monkeypatch.setitem(sys.modules, "src.cleaner", cleaner_package)
    monkeypatch.setitem(sys.modules, "src.cleaner.pipeline", cleaner_module)
    project.config["modules"]["clean"] = "src.pipeline.adapters:cleaner"
    project.config["paths"]["clean"] = "clean.jsonl"
    project.config["options"]["clean"] = {"location_mapping_path": "mapping.csv"}
    save_config(project)
    run_pipeline(project.path, "clean")
    assert forwarded == {"input_path": project.root / "raw.jsonl", "options": {"location_mapping_path": "mapping.csv"}}


def test_cli_failure_returns_nonzero_and_actionable_error(project):
    project.config["modules"]["clean"] = "missing_handoff_module:run"
    save_config(project)
    completed = subprocess.run([sys.executable, "-m", "src.pipeline", "--config", str(project.path), "--stage", "clean"],
                               cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, encoding="utf-8")
    assert completed.returncode == 1
    assert "Không nạp được module clean" in completed.stderr


def test_requirements_only_job_is_valid(project):
    project.raw[0]["job_description"] = None
    project.clean[0].update(job_description=None, job_text="Python")
    jsonl(project.root / "raw.jsonl", project.raw)
    jsonl(project.root / "clean_fixture.jsonl", project.clean)
    assert run_pipeline(project.path, "clean")["status"] == "completed"


def test_no_detected_skills_is_empty_list_not_null(project):
    for row in project.skills:
        row.update(extracted_skills=[], skill_count=0)
    for row in project.matrix:
        row.update(SK1=0, SK2=0)
    jsonl(project.root / "skills_fixture.jsonl", project.skills)
    jsonl(project.root / "matrix_fixture.jsonl", project.matrix)
    assert run_pipeline(project.path)["counts"]["skill_records"] == 2


def test_parquet_typed_dates_preserve_source_values(project):
    for row in project.raw:
        row["posted_date"] = "2026-10-02"
    jsonl(project.root / "raw.jsonl", project.raw)
    def typed_cleaner(ctx):
        rows = [{**row, "crawl_timestamp": datetime.fromisoformat(row["crawl_timestamp"]),
                 "posted_date": date(2026, 10, 2)} for row in project.clean]
        parquet(ctx.paths["clean"], rows)
    project.module.clean = typed_cleaner
    assert run_pipeline(project.path, "clean")["status"] == "completed"


def test_empty_cleaner_output_is_rejected(project):
    project.config["paths"]["clean"] = "clean.jsonl"
    save_config(project)
    project.module.clean = lambda ctx: ctx.paths["clean"].write_text("", encoding="utf-8")
    with pytest.raises(PipelineError, match="bảng rỗng"):
        run_pipeline(project.path, "clean")


@pytest.mark.parametrize("field,value", [
    ("salary_min", None), ("salary_max", None), ("salary_currency", None),
    ("experience_min_years", None), ("experience_max_years", None),
    ("salary_raw", "Thỏa thuận"), ("education", "Cử nhân"),
])
def test_removed_columns_are_rejected(project, field, value):
    project.config["paths"]["clean"] = "clean.jsonl"
    save_config(project)
    for row in project.clean:
        row[field] = value
    jsonl(project.root / "clean_fixture.jsonl", project.clean)
    with pytest.raises(PipelineError, match=f"ngoài schema 22 trường: {field}"):
        run_pipeline(project.path, "clean")


@pytest.mark.parametrize("experience", ["2–4 years of experience", "Fresh graduates are welcome", None])
def test_experience_schema_keeps_only_original_text(project, experience):
    project.raw[0]["raw_experience"] = experience
    project.clean[0]["raw_experience"] = experience
    jsonl(project.root / "raw.jsonl", project.raw)
    jsonl(project.root / "clean_fixture.jsonl", project.clean)
    run_pipeline(project.path, "clean")
    row = pq.read_table(project.root / "clean.parquet").to_pylist()[0]
    assert row["raw_experience"] == experience
    assert len(row) == 22
    assert {field for field in row if "experience" in field} == {"raw_experience"}


def test_source_text_with_salary_or_education_is_preserved(project):
    text = "Lương 20 - 30 triệu VNĐ. Yêu cầu bằng cử nhân và SQL."
    project.raw[0]["job_requirements"] = text
    project.clean[0].update(job_requirements=text, job_text="SQL\n" + text)
    jsonl(project.root / "raw.jsonl", project.raw)
    jsonl(project.root / "clean_fixture.jsonl", project.clean)
    run_pipeline(project.path, "clean")
    row = pq.read_table(project.root / "clean.parquet").to_pylist()[0]
    assert row["job_requirements"] == text
    assert "salary_raw" not in row and "education" not in row
