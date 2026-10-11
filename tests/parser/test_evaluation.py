import json
from pathlib import Path

import pytest

from src.parser.evaluation import evaluate_file, metrics, score_predictions, verify_independence
from src.parser.features import read_jobs
from src.parser.skill_extractor import DEFAULT_TAXONOMY


ROOT = DEFAULT_TAXONOMY.parents[1]


def test_metric_formula():
    result = metrics(420, 35, 50)
    assert result["precision"] == pytest.approx(420 / 455)
    assert result["recall"] == pytest.approx(420 / 470)
    assert result["f1"] == pytest.approx(840 / 925)
    assert metrics(0, 0, 0)["f1"] == 0


def test_multilabel_sets_and_errors():
    result = score_predictions({"a": ["Python", "SQL"], "b": []}, {"a": ["Python", "Docker"], "b": []})
    assert result["micro"]["tp"] == result["micro"]["fp"] == result["micro"]["fn"] == 1
    assert result["errors"] == [{"job_id": "a", "false_positives": ["Docker"], "false_negatives": ["SQL"]}]
    with pytest.raises(ValueError, match="job_id"):
        score_predictions({"a": []}, {})


def test_gold_evaluation_is_marked_draft(tmp_path):
    report = evaluate_file(ROOT / "data/evaluation/gold_jobs.draft.jsonl", tmp_path, DEFAULT_TAXONOMY,
                           ROOT / "data/sample/sample_jobs.jsonl")
    assert report["jobs"] == 50
    assert report["evaluation_kind"] == "assistant_annotated_draft"
    assert report["human_reviewed"] is False and report["research_acceptance"] is False
    assert report["gold_annotations"] == report["micro"]["tp"] + report["micro"]["fn"]


@pytest.mark.parametrize("mutation", [
    lambda r: r.update(gold_skills=["Invented Skill"]),
    lambda r: r.update(annotation_status="pending"),
    lambda r: r.update(annotation_status="human_reviewed", human_reviewed=False),
    lambda r: r.update(text="changed"),
    lambda r: r["annotations"][0].update(evidence="changed"),
    lambda r: r["annotations"][0].update(skill_id="changed"),
])
def test_invalid_gold_is_rejected(tmp_path, mutation):
    rows = read_jobs(ROOT / "data/evaluation/gold_jobs.draft.jsonl")
    mutation(rows[0])
    gold = tmp_path / "invalid.jsonl"
    gold.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    with pytest.raises(ValueError):
        evaluate_file(gold, tmp_path / "report", DEFAULT_TAXONOMY, ROOT / "data/sample/sample_jobs.jsonl")
    assert not (tmp_path / "report").exists()


@pytest.mark.parametrize("key", ["job_id", "source_url", "source_job_id"])
def test_reference_overlap_is_rejected(key):
    reference = dict(job_id="original", source_url="url", source_job_id="id", job_description="Text long enough to compare shingles")
    row = dict(job_id="new", source_url="other", source_job_id="other", job_description="Completely distinct skill description for another role")
    row[key] = reference[key]
    with pytest.raises(ValueError, match="trùng ID/URL"):
        verify_independence([row], [reference])


def test_near_duplicate_is_rejected():
    with pytest.raises(ValueError, match="gần trùng"):
        verify_independence([dict(job_id="new", job_description="Python SQL Docker and Kafka experience")],
                            [dict(job_id="old", job_description="Python SQL Docker and Kafka experience")])


def test_reports_cannot_overwrite_gold(tmp_path):
    gold = tmp_path / "errors.jsonl"
    gold.write_text((ROOT / "data/evaluation/gold_jobs.draft.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    before = gold.read_bytes()
    with pytest.raises(ValueError, match="ghi đè"):
        evaluate_file(gold, tmp_path, DEFAULT_TAXONOMY, ROOT / "data/sample/sample_jobs.jsonl")
    assert gold.read_bytes() == before
