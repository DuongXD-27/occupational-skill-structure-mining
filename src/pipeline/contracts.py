"""Kiểm tra schema, tính toàn vẹn và quan hệ khóa giữa các đầu ra."""

import csv
from datetime import date, datetime
import json
from pathlib import Path

from .config import PipelineError


FIELDS = (
    "job_id source source_job_id source_url crawl_timestamp parser_version raw_job_title "
    "normalized_job_title company raw_location normalized_location posted_date raw_experience "
    "job_description job_requirements job_text relevance_flag exclusion_reason "
    "duplicate_flag duplicate_group_id extracted_skills skill_count"
).split()
BOOLS = {"relevance_flag", "duplicate_flag"}
RAW_FIELDS = (
    "source source_job_id source_url crawl_timestamp parser_version raw_job_title company "
    "raw_location raw_experience job_description job_requirements posted_date"
).split()


def fail(stage, path, message):
    raise PipelineError(f"Không thể chạy {stage}: {message} trong {path}.")


def read_table(path: Path, stage: str) -> list[dict]:
    if not path.is_file():
        fail(stage, path, "không tìm thấy file đầu vào/đầu ra")
    try:
        if path.suffix.lower() == ".jsonl":
            rows = []
            for line_no, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
                if line.strip():
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        fail(stage, path, f"dòng {line_no} phải là object JSON")
                    rows.append(row)
            return rows
        import pyarrow.parquet as pq
        return pq.read_table(path).to_pylist()
    except PipelineError:
        raise
    except Exception as exc:
        fail(stage, path, f"không đọc được bảng ({exc})")


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def check_columns(rows, required, stage, path, *, exact=False):
    if not rows:
        fail(stage, path, "bảng rỗng; không có bản ghi để chuyển bước")
    for index, row in enumerate(rows, 1):
        for field in required:
            if field not in row:
                fail(stage, path, f"thiếu trường {field} ở dòng {index}")
        if exact and (extra := set(row) - set(required)):
            fail(stage, path, f"trường ngoài schema {len(required)} trường: {', '.join(sorted(extra))}")


def unique_ids(rows, stage, path):
    seen = set()
    for index, row in enumerate(rows, 1):
        key = row.get("job_id")
        if not nonempty(key):
            fail(stage, path, f"job_id phải là chuỗi không rỗng ở dòng {index}")
        if key in seen:
            fail(stage, path, f"job_id bị lặp: {key}")
        seen.add(key)
    return seen


def eligible(rows):
    return [r for r in rows if r["relevance_flag"] is True and r["duplicate_flag"] is False]


def validate_jobs(path: Path, stage: str, *, cleaned=False):
    rows = read_table(path, stage)
    check_columns(rows, FIELDS, stage, path, exact=True)
    unique_ids(rows, stage, path)
    for row in rows:
        key = row["job_id"]
        for field in FIELDS:
            value = row[field]
            if value is None:
                continue
            if field in BOOLS:
                valid = type(value) is bool
            elif field == "skill_count":
                valid = type(value) is int and value >= 0
            elif field == "extracted_skills":
                valid = isinstance(value, list) and all(nonempty(v) for v in value)
            elif field == "crawl_timestamp":
                valid = isinstance(value, (str, datetime))
            elif field == "posted_date":
                valid = isinstance(value, str) or type(value) is date
            else:
                valid = isinstance(value, str)
            if not valid:
                fail(stage, path, f"sai kiểu/giá trị trường {field}, job_id={key}")
        for field in ("source", "source_url", "crawl_timestamp", "parser_version", "raw_job_title"):
            if field == "crawl_timestamp" and isinstance(row[field], datetime):
                continue
            if not nonempty(row[field]):
                fail(stage, path, f"trường {field} rỗng, job_id={key}")
        try:
            if isinstance(row["crawl_timestamp"], str):
                datetime.fromisoformat(row["crawl_timestamp"].replace("Z", "+00:00"))
            if isinstance(row["posted_date"], str):
                date.fromisoformat(row["posted_date"])
        except ValueError:
            fail(stage, path, f"ngày/dấu thời gian không đúng ISO 8601, job_id={key}")
        if not (nonempty(row["job_description"]) or nonempty(row["job_requirements"])):
            fail(stage, path, f"thiếu cả job_description và job_requirements, job_id={key}")
        if cleaned:
            for field in BOOLS:
                if type(row[field]) is not bool:
                    fail(stage, path, f"{field} chưa được gán boolean, job_id={key}")
            if row["relevance_flag"] is False and not nonempty(row["exclusion_reason"]):
                fail(stage, path, f"thiếu exclusion_reason cho tin bị loại, job_id={key}")
            if row["relevance_flag"] and not row["duplicate_flag"]:
                for field in ("normalized_job_title", "job_text"):
                    if not nonempty(row[field]):
                        fail(stage, path, f"thiếu {field} cho tin hợp lệ, job_id={key}")
    return rows


def validate_preservation(raw, clean, path):
    by_id = {r["job_id"]: r for r in raw}
    if set(by_id) != {r["job_id"] for r in clean}:
        fail("cleaner", path, "cleaner làm mất/thêm job_id; phải giữ bản ghi và đánh cờ")
    for row in clean:
        for field in RAW_FIELDS:
            before, after = by_id[row["job_id"]][field], row[field]
            # Parquet có thể lưu date/timestamp có kiểu thay cho chuỗi ISO nguồn.
            if field == "crawl_timestamp" and isinstance(after, datetime) and isinstance(before, str):
                before = datetime.fromisoformat(before.replace("Z", "+00:00"))
            elif field == "posted_date" and type(after) is date and isinstance(before, str):
                before = date.fromisoformat(before)
            if after != before:
                fail("cleaner", path, f"ghi đè trường gốc {field}, job_id={row['job_id']}")


def read_taxonomy(path):
    try:
        with path.open(encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
    except OSError as exc:
        fail("skill extraction", path, f"không đọc được taxonomy ({exc})")
    check_columns(rows, ("skill_id", "canonical_name"), "skill extraction", path)
    mapping = {}
    for row in rows:
        key, name = row["skill_id"], row["canonical_name"]
        if not nonempty(key) or not nonempty(name) or key in mapping or name in mapping.values():
            fail("skill extraction", path, "skill_id/canonical_name rỗng hoặc trùng lặp")
        mapping[key] = name
    return mapping


def validate_features(clean, skills_path, matrix_path, taxonomy):
    stage = "analysis"
    skills = read_table(skills_path, stage)
    matrix = read_table(matrix_path, stage)
    check_columns(skills, ("job_id", "extracted_skills", "skill_count"), stage, skills_path)
    check_columns(matrix, ("job_id",), stage, matrix_path)
    expected = {r["job_id"] for r in eligible(clean)}
    for rows, path in ((skills, skills_path), (matrix, matrix_path)):
        if unique_ids(rows, stage, path) != expected:
            fail(stage, path, "job_id phải khớp đúng tập relevance=true và duplicate=false")
    names = set(taxonomy.values())
    by_id = {}
    for row in skills:
        values = row["extracted_skills"]
        if not isinstance(values, list) or not all(nonempty(v) for v in values):
            fail(stage, skills_path, f"extracted_skills phải là list[string], job_id={row['job_id']}")
        if len(set(values)) != len(values) or not set(values) <= names:
            fail(stage, skills_path, f"kỹ năng trùng/ngoài taxonomy, job_id={row['job_id']}")
        if type(row["skill_count"]) is not int or row["skill_count"] != len(values):
            fail(stage, skills_path, f"skill_count không khớp danh sách, job_id={row['job_id']}")
        by_id[row["job_id"]] = set(values)
    columns = set(matrix[0]) - {"job_id"}
    if not columns or not columns <= set(taxonomy):
        fail(stage, matrix_path, "cột kỹ năng phải dùng skill_id của taxonomy đang hoạt động")
    for row in matrix:
        if set(row) != columns | {"job_id"}:
            fail(stage, matrix_path, "các dòng ma trận không cùng schema")
        detected = set()
        for skill in columns:
            value = row[skill]
            if type(value) is not int or value not in (0, 1):
                fail(stage, matrix_path, f"ô {skill} phải là số nguyên 0/1, job_id={row['job_id']}")
            if value == 1:
                detected.add(taxonomy[skill])
        if detected != by_id[row["job_id"]]:
            fail(stage, matrix_path, f"ma trận không khớp extracted_skills, job_id={row['job_id']}")
    return skills, matrix


def validate_rq_result(result, questions, directory):
    if not isinstance(result, dict) or set(result) != set(questions):
        fail("analysis", directory, f"module phải trả đúng trạng thái {', '.join(questions)}")
    for rq, item in result.items():
        if not isinstance(item, dict) or item.get("status") not in ("completed", "skipped"):
            fail(rq, directory, "status phải là completed hoặc skipped")
        if item["status"] == "skipped" and not nonempty(item.get("reason")):
            fail(rq, directory, "RQ bị bỏ qua phải có reason")
        artifacts = item.get("artifacts", [])
        if not isinstance(artifacts, list) or not all(nonempty(a) for a in artifacts):
            fail(rq, directory, "artifacts phải là danh sách đường dẫn tương đối")
        if item["status"] == "completed" and not artifacts:
            fail(rq, directory, "RQ completed phải có file kết quả")
        for artifact in artifacts:
            path = (directory / artifact).resolve()
            if Path(artifact).is_absolute() or directory.resolve() not in path.parents:
                fail(rq, directory, f"artifact nằm ngoài thư mục đầu ra: {artifact}")
            if not path.is_file() or path.stat().st_size == 0:
                fail(rq, directory, f"artifact không tồn tại hoặc rỗng: {artifact}")
