"""Tính toán lại tần suất xuất hiện tài liệu (document frequency) của taxonomy từ tập mẫu dữ liệu chính thức."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


# Hỗ trợ cả python scripts/recount_taxonomy.py và import từ repository.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.parser.skill_extractor import (
    FIELDNAMES, TEXT_FIELDS, load_taxonomy, normalize_text, contains_term,
    term_matches, split_terms, abbreviation_is_supported,
    skill_match_candidates, extract_document_skills, document_text,
)

EVIDENCE_FIELDNAMES = [
    "skill_id",
    "canonical_name",
    "job_id",
    "match_type",
    "matched_term",
]

def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--jobs",
        type=Path,
        default=repo_root / "data" / "sample" / "sample_jobs.jsonl",
    )
    parser.add_argument(
        "--taxonomy",
        type=Path,
        default=repo_root / "taxonomy" / "skills_taxonomy.csv",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--evidence-output", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--expected-job-count", type=int, default=45)
    parser.add_argument("--expected-source", default="ITviec")
    args = parser.parse_args()
    if args.check and args.output:
        parser.error("--check và --output không thể sử dụng đồng thời")
    return args


def load_jobs(path: Path, expected_count: int, expected_source: str) -> list[dict]:
    jobs = []
    with path.open(encoding="utf-8-sig") as jsonl_file:
        for line_number, line in enumerate(jsonl_file, start=1):
            if not line.strip():
                continue
            try:
                job = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON on {path}:{line_number}: {error}") from error
            jobs.append(job)

    if len(jobs) != expected_count:
        raise ValueError(
            f"Expected {expected_count} jobs in {path}, found {len(jobs)}"
        )

    unexpected_sources = sorted(
        {job.get("source") for job in jobs if job.get("source") != expected_source}
    )
    if unexpected_sources:
        raise ValueError(
            f"Expected only source {expected_source!r}; found {unexpected_sources!r}"
        )

    job_ids = [job.get("job_id") for job in jobs]
    if any(not job_id for job_id in job_ids):
        raise ValueError("Every job must have a non-empty job_id")
    if len(job_ids) != len(set(job_ids)):
        raise ValueError("job_id values must be unique")
    return jobs



def recount(
    rows: list[dict[str, str]], jobs: list[dict]
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    documents = []
    for job in jobs:
        text = document_text(job)
        documents.append((job["job_id"], text))

    counts = {row["skill_id"]: 0 for row in rows}
    evidence_rows = []
    for job_id, text in documents:
        for match in extract_document_skills(rows, text):
            skill_id = str(match["skill_id"])
            counts[skill_id] += 1
            evidence_rows.append(
                {
                    "skill_id": skill_id,
                    "canonical_name": str(match["canonical_name"]),
                    "job_id": job_id,
                    "match_type": str(match["match_type"]),
                    "matched_term": str(match["matched_term"]),
                }
            )

    recounted_rows = []
    for row in rows:
        if counts[row["skill_id"]] == 0:
            continue
        updated = dict(row)
        updated["observed_count"] = str(counts[row["skill_id"]])
        recounted_rows.append(updated)
    return recounted_rows, evidence_rows


def render_csv(rows: list[dict[str, str]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDNAMES, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def render_evidence_csv(rows: list[dict[str, str]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output, fieldnames=EVIDENCE_FIELDNAMES, lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def main() -> int:
    args = parse_args()
    try:
        jobs = load_jobs(args.jobs, args.expected_job_count, args.expected_source)
        rows = load_taxonomy(args.taxonomy)
        recounted_rows, evidence_rows = recount(rows, jobs)
        rendered = render_csv(recounted_rows)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.check:
        current = args.taxonomy.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        if current != rendered:
            print(
                "Lỗi: các giá trị observed_count trong taxonomy đã cũ; hãy chạy: "
                "python scripts/recount_taxonomy.py",
                file=sys.stderr,
            )
            return 1
        if args.evidence_output:
            try:
                current_evidence = args.evidence_output.read_text(
                    encoding="utf-8-sig"
                ).replace("\r\n", "\n")
            except OSError:
                current_evidence = ""
            if current_evidence != render_evidence_csv(evidence_rows):
                print(
                    "Lỗi: file bằng chứng taxonomy đã cũ; hãy chạy: python "
                    "scripts/recount_taxonomy.py --evidence-output "
                    "reports/skill_extraction/skills_taxonomy_evidence.csv",
                    file=sys.stderr,
                )
                return 1
        print(f"Taxonomy đã được cập nhật chuẩn xác cho {len(jobs)} tin tuyển dụng {args.expected_source}.")
        return 0

    output_path = args.output or args.taxonomy
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8", newline="")
    if args.evidence_output:
        args.evidence_output.parent.mkdir(parents=True, exist_ok=True)
        args.evidence_output.write_text(
            render_evidence_csv(evidence_rows), encoding="utf-8", newline=""
        )
    print(
        f"Đã ghi nhận {len(recounted_rows)} kỹ năng quan sát được trên tổng số "
        f"{len(jobs)} tin vào {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
