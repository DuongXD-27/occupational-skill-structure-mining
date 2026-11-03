"""Chọn tin độc lập để gán nhãn; không tạo nhãn bằng output parser."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.parser.evaluation import shingles, similarity
from src.parser.features import read_jobs
from src.parser.skill_extractor import document_text


def select_candidates(rows, reference, limit=50):
    known = {k: {r.get(k) for r in reference if r.get(k)} for k in ("job_id", "source_url", "source_job_id")}
    seen = [shingles(r) for r in reference]
    chosen = []
    for row in sorted(rows, key=lambda r: (len(document_text(r)), r["job_id"])):
        if any(row.get(k) in values for k, values in known.items()):
            continue
        if not re.search(r"data|\bAI\b|machine learning|business intelligence", row.get("raw_job_title") or "", re.I):
            continue
        if len(document_text(row)) < 150:
            continue
        tokens = shingles(row)
        if any(similarity(tokens, other) >= .5 for other in seen):
            continue
        chosen.append(row)
        seen.append(tokens)
        for key, values in known.items():
            if row.get(key):
                values.add(row[key])
        if len(chosen) == limit:
            break
    return chosen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--reference", type=Path, default=Path(__file__).resolve().parents[1] / "data/sample/sample_jobs.jsonl")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit phải dương")
    if args.output.resolve() in (args.input.resolve(), args.reference.resolve()):
        parser.error("Output không được ghi đè input/reference")
    try:
        chosen = select_candidates(read_jobs(args.input), read_jobs(args.reference), args.limit)
        if len(chosen) < args.limit:
            raise ValueError(f"Chỉ có {len(chosen)} tin độc lập, cần {args.limit}.")
        pending = []
        for row in chosen:
            text = document_text(row)
            pending.append({**{k: row.get(k) for k in ("job_id", "source", "source_job_id", "source_url", "crawl_timestamp",
                                                     "raw_job_title", "job_description", "job_requirements")},
                            "text": text, "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                            "annotation_status": "pending", "annotated_by": None, "human_reviewed": False,
                            "gold_skills": None, "annotations": []})
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in pending), encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")
    print(f"Đã chọn {len(pending)} tin chờ gán nhãn: {args.output}")


if __name__ == "__main__":
    main()
