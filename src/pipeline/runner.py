"""Chạy từng bước hoặc toàn chuỗi, kiểm tra đầu ra rồi xuất báo cáo."""

from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import tempfile
from types import MappingProxyType

from .config import PipelineError, STAGES, StageContext, load_config
from .contracts import (
    eligible, read_taxonomy, validate_features, validate_jobs,
    validate_preservation, validate_rq_result,
)


OUTPUTS = {"clean": ("clean",), "extract": ("skills", "matrix"), "rq1": ("rq1",), "analysis": ("analysis",)}
INPUTS = {"clean": ("raw",), "rq1": ("clean",), "extract": ("clean", "taxonomy"),
          "analysis": ("clean", "skills", "matrix", "taxonomy")}
QUESTIONS = {"rq1": ("RQ1",), "analysis": ("RQ2", "RQ3", "RQ4")}


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def resolve_module(config, stage):
    entry = config.modules.get(stage)
    if not entry:
        raise PipelineError(f"Chưa bàn giao module {stage}: cấu hình modules.{stage} = null.")
    module, name = entry.split(":")
    try:
        function = getattr(importlib.import_module(module), name)
    except (ImportError, AttributeError) as exc:
        raise PipelineError(f"Không nạp được module {stage} ({entry}): {exc}") from exc
    if not callable(function):
        raise PipelineError(f"Entry point {entry} không phải hàm callable.")
    return function


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    # File tạm cùng thư mục cho phép replace trên cùng ổ đĩa.
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     suffix=".tmp", delete=False) as file:
        temporary = Path(file.name)
        json.dump(value, file, ensure_ascii=False, indent=2)
        file.write("\n")
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def clean_counts(rows):
    duplicates = sum(r["duplicate_flag"] for r in rows)
    outside = sum(not r["relevance_flag"] for r in rows)
    overlap = sum(r["duplicate_flag"] and not r["relevance_flag"] for r in rows)
    return {"clean_records": len(rows), "valid_records": len(eligible(rows)),
            "duplicates": duplicates, "out_of_scope": outside, "overlap": overlap}


def validate_inputs(config, stage):
    paths = config.paths
    if stage == "clean":
        rows = validate_jobs(paths["raw"], "cleaner")
        return {"raw_records": len(rows)}, rows, None
    rows = validate_jobs(paths["clean"], "skill extraction" if stage == "extract" else stage, cleaned=True)
    if not eligible(rows):
        raise PipelineError(f"Không thể chạy {stage}: không có tin hợp lệ sau làm sạch.")
    taxonomy = read_taxonomy(paths["taxonomy"]) if stage in ("extract", "analysis") else None
    counts = clean_counts(rows)
    if stage == "analysis":
        skills, matrix = validate_features(rows, paths["skills"], paths["matrix"], taxonomy)
        counts.update(skill_records=len(skills), matrix_rows=len(matrix))
    return counts, rows, taxonomy


def publish(source, target):
    if source.is_dir():
        for file in sorted(source.rglob("*")):
            if file.is_file():
                destination = target / file.relative_to(source)
                destination.parent.mkdir(parents=True, exist_ok=True)
                file.replace(destination)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        source.replace(target)


def run_stage(config, stage, report):
    counts, inputs, taxonomy = validate_inputs(config, stage)
    report["counts"].update(counts)
    function = resolve_module(config, stage)
    fingerprints = {key: digest(config.paths[key]) for key in INPUTS[stage]}
    report["stages"][stage]["inputs"] = {
        key: {"path": str(config.paths[key]), "sha256": value}
        for key, value in fingerprints.items()
    }
    # Kết quả cũ không thể được dùng để giả lập một lần chạy thành công.
    first_target = config.paths[OUTPUTS[stage][0]]
    first_target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".pipeline-", dir=first_target.parent) as scratch:
        paths = dict(config.paths)
        for key in OUTPUTS[stage]:
            target = config.paths[key]
            paths[key] = Path(scratch) / (key + target.suffix if stage not in QUESTIONS else key)
            if stage in QUESTIONS:
                paths[key].mkdir()
        context = StageContext(stage, MappingProxyType(paths), MappingProxyType(config.options.get(stage, {})))
        try:
            result = function(context)
        except Exception as exc:
            raise PipelineError(f"Module {stage} thất bại ({config.modules[stage]}): {exc}") from exc
        finally:
            for key, value in fingerprints.items():
                if not config.paths[key].is_file() or digest(config.paths[key]) != value:
                    raise PipelineError(f"Module {stage} đã sửa đầu vào chỉ đọc: {config.paths[key]}")
        if stage == "clean":
            rows = validate_jobs(paths["clean"], "cleaner output", cleaned=True)
            validate_preservation(inputs, rows, paths["clean"])
            report["counts"].update(clean_counts(rows))
        elif stage == "extract":
            skills, matrix = validate_features(inputs, paths["skills"], paths["matrix"], taxonomy)
            report["counts"].update(skill_records=len(skills), matrix_rows=len(matrix))
        else:
            validate_rq_result(result, QUESTIONS[stage], paths[stage])
            write_json(paths[stage] / "manifest.json", result)
        for key in OUTPUTS[stage]:
            publish(paths[key], config.paths[key])
        if stage in QUESTIONS:
            for rq, item in result.items():
                report["rq"][rq].update(**item, directory=str(config.paths[stage]))
        report["stages"][stage]["outputs"] = {
            key: str(config.paths[key]) for key in OUTPUTS[stage]
        }


def run_pipeline(config_path: str | Path, stage="all"):
    config = load_config(config_path)
    if stage not in (*STAGES, "all"):
        raise PipelineError(f"Bước không hợp lệ: {stage}")
    selected = STAGES if stage == "all" else (stage,)
    report = {
        "started_at": timestamp(), "config": str(config.file), "stage": stage,
        "run_kind": config.run_kind, "config_sha256": digest(config.file),
        "status": "running", "counts": {},
        "stages": {s: {"status": "not_run"} for s in STAGES},
        "rq": {rq: {"status": "not_run", "owner": owner}
               for rq, owner in (("RQ1", "Đức"), ("RQ2", "Triều"), ("RQ3", "Triều"), ("RQ4", "Triều"))},
    }
    try:
        for current in selected:
            report["stages"][current] = {"status": "running", "started_at": timestamp(),
                                        "module": config.modules.get(current)}
            try:
                run_stage(config, current, report)
            except Exception as exc:
                report["stages"][current].update(status="failed", error=str(exc), finished_at=timestamp())
                for rq in QUESTIONS.get(current, ()):
                    report["rq"][rq].update(status="failed", reason=str(exc))
                raise
            report["stages"][current].update(status="completed", finished_at=timestamp())
        report["status"] = "completed"
    except Exception as exc:
        report.update(status="failed", error=str(exc))
        if isinstance(exc, PipelineError):
            raise
        raise PipelineError(str(exc)) from exc
    finally:
        report["finished_at"] = timestamp()
        report["research_acceptance"] = config.run_kind == "research" and stage == "all" and report["status"] == "completed" and all(
            r["status"] == "completed" for r in report["rq"].values()
        )
        write_json(config.paths["report"], report)
    return report
