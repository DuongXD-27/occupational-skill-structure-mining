"""Xuất danh sách canonical names và ma trận skill_id cho module phân tích."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile

from .skill_extractor import DEFAULT_TAXONOMY, SkillExtractor, document_text


def read_jobs(path: str | Path) -> list[dict]:
    path = Path(path)
    if path.suffix.lower() == ".jsonl":
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    elif path.suffix.lower() == ".parquet":
        import pyarrow.parquet as pq
        rows = pq.read_table(path).to_pylist()
    else:
        raise ValueError("Đầu vào phải là JSONL hoặc Parquet.")
    ids = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("job_id"), str) or not row["job_id"].strip():
            raise ValueError("Mỗi tin phải có job_id string không rỗng.")
        ids.append(row["job_id"])
        for field in ("raw_job_title", "job_description", "job_requirements"):
            if row.get(field) is not None and not isinstance(row[field], str):
                raise ValueError(f"{field} phải là string/null.")
    if not rows or len(set(ids)) != len(ids):
        raise ValueError("Đầu vào rỗng hoặc job_id bị lặp.")
    return rows


def feature_rows(jobs: list[dict], extractor: SkillExtractor, *, preview: bool = False):
    if not preview:
        for row in jobs:
            if type(row.get("relevance_flag")) is not bool or type(row.get("duplicate_flag")) is not bool:
                raise ValueError("Artifact chính thức cần relevance_flag/duplicate_flag boolean từ cleaner.")
        jobs = [r for r in jobs if r["relevance_flag"] and not r["duplicate_flag"]]
    if not jobs:
        raise ValueError("Không có tin hợp lệ để trích xuất.")
    skills, matrix = [], []
    for row in jobs:
        if not any((row.get(field) or "").strip() for field in ("job_description", "job_requirements")):
            raise ValueError(f"Tin {row['job_id']} thiếu mô tả và yêu cầu.")
        names = extractor.extract(document_text(row))
        present = set(names)
        skills.append({"job_id": row["job_id"], "extracted_skills": names, "skill_count": len(names)})
        matrix.append({"job_id": row["job_id"], **{
            r["skill_id"]: int(r["canonical_name"] in present) for r in extractor.rows
        }})
    return skills, matrix


def export_features(clean_path, skills_path, matrix_path, taxonomy_path=DEFAULT_TAXONOMY, *, preview=False):
    import pyarrow as pa
    import pyarrow.parquet as pq
    inputs = [Path(clean_path).resolve(), Path(taxonomy_path).resolve()]
    outputs = [Path(skills_path).resolve(), Path(matrix_path).resolve()]
    if outputs[0] == outputs[1] or any(p in inputs for p in outputs):
        raise ValueError("Đường dẫn đầu ra không được trùng nhau hoặc ghi đè input/taxonomy.")
    if any(path.suffix.lower() != ".parquet" for path in outputs):
        raise ValueError("Đầu ra đặc trưng phải là file .parquet.")
    extractor = SkillExtractor(inputs[1])
    jobs = read_jobs(inputs[0])
    skills, matrix = feature_rows(jobs, extractor, preview=preview)
    skill_schema = pa.schema([("job_id", pa.string()), ("extracted_skills", pa.list_(pa.string())),
                              ("skill_count", pa.int32())])
    matrix_schema = pa.schema([("job_id", pa.string()), *[(r["skill_id"], pa.uint8()) for r in extractor.rows]])
    tables = [pa.Table.from_pylist(skills, schema=skill_schema), pa.Table.from_pylist(matrix, schema=matrix_schema)]
    # Ghi xong cả hai file tạm trước khi thay đầu ra cũ. Replace hai file không là giao dịch nguyên tử.
    temporary = []
    try:
        for target, table in zip(outputs, tables):
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".parquet", delete=False) as file:
                temp = Path(file.name)
            temporary.append(temp)
            pq.write_table(table, temp)
        for temp, target in zip(temporary, outputs):
            temp.replace(target)
    finally:
        for temp in temporary:
            temp.unlink(missing_ok=True)
    return {"artifact_kind": "raw_preview" if preview else "clean_features",
            "research_acceptance": False, "input_records": len(jobs), "feature_records": len(skills),
            "taxonomy_skills": len(extractor.rows),
            "source_sha256": hashlib.sha256(inputs[0].read_bytes()).hexdigest(),
            "taxonomy_sha256": hashlib.sha256(inputs[1].read_bytes()).hexdigest(),
            "parser_sha256": hashlib.sha256(Path(__file__).with_name("skill_extractor.py").read_bytes()).hexdigest(),
            "text_fields": ["raw_job_title", "job_description", "job_requirements"],
            "selection": "all raw records; development only" if preview else "relevance_flag=true AND duplicate_flag=false"}


def run(context):
    """Entry point src.parser.features:run cho StageContext của PR #15."""
    if "preview" in context.options:
        raise ValueError("Entry point pipeline chỉ nhận dữ liệu sạch; dùng CLI preview để thử raw.")
    return export_features(context.paths["clean"], context.paths["skills"], context.paths["matrix"],
                           context.paths["taxonomy"], **context.options)
