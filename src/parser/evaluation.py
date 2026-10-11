"""Đánh giá tập nhãn độc lập, giữ rõ trạng thái nhãn dự thảo/người rà soát."""
from __future__ import annotations

from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re

from .features import read_jobs
from .skill_extractor import SkillExtractor, document_text


def shingles(row):
    text = " ".join(str(row.get(k) or "") for k in ("job_description", "job_requirements"))
    words = re.findall(r"\w+", text.casefold())
    return {tuple(words[i:i+5]) for i in range(max(1, len(words)-4))}


def similarity(a, b):
    return len(a & b) / len(a | b) if a | b else 1.0


def verify_independence(rows, reference):
    seen = list(reference)
    seen_shingles = [shingles(r) for r in seen]
    for row in rows:
        for previous, tokens in zip(seen, seen_shingles):
            if any(row.get(k) and row.get(k) == previous.get(k) for k in ("job_id", "source_url", "source_job_id")):
                raise ValueError(f"Gold trùng ID/URL với reference hoặc tin khác: {row['job_id']}")
            if similarity(shingles(row), tokens) >= .5:
                raise ValueError(f"Gold có văn bản trùng/gần trùng: {row['job_id']}")
        seen.append(row)
        seen_shingles.append(shingles(row))


def metrics(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def score_predictions(gold, predicted):
    if set(gold) != set(predicted):
        raise ValueError("Tập job_id của gold và predictions phải khớp.")
    counts = Counter()
    per_skill = {}
    errors = []
    for job_id, names in gold.items():
        expected, actual = set(names), set(predicted[job_id])
        tp, fp, fn = expected & actual, actual - expected, expected - actual
        counts.update(tp=len(tp), fp=len(fp), fn=len(fn))
        for kind, values in (("tp", tp), ("fp", fp), ("fn", fn)):
            for name in values:
                per_skill.setdefault(name, Counter())[kind] += 1
        if fp or fn:
            errors.append({"job_id": job_id, "false_positives": sorted(fp), "false_negatives": sorted(fn)})
    return {"micro": metrics(counts["tp"], counts["fp"], counts["fn"]),
            "per_skill": {name: metrics(c["tp"], c["fp"], c["fn"]) for name, c in sorted(per_skill.items())},
            "errors": errors}


def evaluate_file(gold_path, output_dir, taxonomy_path, reference_path):
    gold_path, output_dir = Path(gold_path), Path(output_dir)
    inputs = {Path(p).resolve() for p in (gold_path, taxonomy_path, reference_path)}
    if any((output_dir / name).resolve() in inputs for name in ("metrics.json", "errors.jsonl", "per_skill.csv", "predictions.jsonl")):
        raise ValueError("Báo cáo không được ghi đè gold/taxonomy/reference.")
    extractor = SkillExtractor(taxonomy_path)
    rows = read_jobs(gold_path)
    verify_independence(rows, read_jobs(reference_path))
    by_name = {r["canonical_name"]: r["skill_id"] for r in extractor.rows}
    for row in rows:
        text = document_text(row)
        if row.get("text") != text or row.get("text_sha256") != hashlib.sha256(text.encode()).hexdigest():
            raise ValueError(f"Gold text/hash không khớp nguồn: {row['job_id']}")
        names = row.get("gold_skills")
        if not isinstance(names, list) or any(not isinstance(n, str) or n not in by_name for n in names) or len(set(names)) != len(names):
            raise ValueError("Gold labels phải là canonical names duy nhất trong taxonomy.")
        if row.get("annotation_status") not in ("assistant_annotated_draft", "human_reviewed") or not row.get("annotated_by"):
            raise ValueError("Gold chưa có nhãn hoặc thiếu nguồn gán nhãn.")
        if row.get("annotation_status") == "human_reviewed" and row.get("human_reviewed") is not True:
            raise ValueError("Trạng thái human_reviewed không khớp metadata.")
        annotations = row.get("annotations")
        if (not isinstance(annotations, list) or len(annotations) != len(names)
                or any(not isinstance(a, dict) or not isinstance(a.get("canonical_name"), str) for a in annotations)
                or {a.get("canonical_name") for a in annotations} != set(names)):
            raise ValueError("Mỗi gold label phải có đúng một annotation bằng chứng.")
        for annotation in annotations:
            a, b = annotation.get("start"), annotation.get("end")
            if type(a) is not int or type(b) is not int or not 0 <= a < b <= len(text):
                raise ValueError("Gold evidence span không hợp lệ.")
            if text[a:b] != annotation.get("evidence") or by_name[annotation["canonical_name"]] != annotation.get("skill_id"):
                raise ValueError("Gold evidence/skill_id không khớp.")
    predictions = {r["job_id"]: extractor.extract(r["text"]) for r in rows}
    scored = score_predictions({r["job_id"]: r["gold_skills"] for r in rows}, predictions)
    human_reviewed = all(r["annotation_status"] == "human_reviewed" and r.get("human_reviewed") is True for r in rows)
    report = {"evaluation_kind": "human_reviewed_gold" if human_reviewed else "assistant_annotated_draft",
              "research_acceptance": False, "human_reviewed": human_reviewed,
              "jobs": len(rows), "gold_annotations": sum(len(r["gold_skills"]) for r in rows),
              "prediction_annotations": sum(len(p) for p in predictions.values()),
              "jobs_with_errors": len(scored["errors"]), "micro": scored["micro"],
              "scoring_scope": "canonical skills in frozen taxonomy; OOV concepts excluded",
              "independence": "distinct job_id/source_url/source_job_id; 5-word shingle Jaccard < 0.5 against sample and other gold records",
              "gold_sha256": hashlib.sha256(gold_path.read_bytes()).hexdigest(),
              "taxonomy_sha256": hashlib.sha256(Path(taxonomy_path).read_bytes()).hexdigest(),
              "parser_sha256": hashlib.sha256(Path(__file__).with_name("skill_extractor.py").read_bytes()).hexdigest(),
              "reference_sha256": hashlib.sha256(Path(reference_path).read_bytes()).hexdigest()}
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "metrics.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "errors.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in scored["errors"]), encoding="utf-8")
    with (output_dir / "per_skill.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["canonical_name", "tp", "fp", "fn", "precision", "recall", "f1"])
        writer.writeheader()
        writer.writerows({"canonical_name": name, **values} for name, values in scored["per_skill"].items())
    (output_dir / "predictions.jsonl").write_text("".join(json.dumps({"job_id": k, "extracted_skills": v}, ensure_ascii=False) + "\n" for k, v in predictions.items()), encoding="utf-8")
    return report
