import csv
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import recount_taxonomy
from src.parser import SkillExtractor, extract_skills
from src.parser.skill_extractor import DEFAULT_TAXONOMY, document_text, normalize_text


@pytest.fixture(scope="module")
def extractor():
    return SkillExtractor()


@pytest.mark.parametrize("text,expected", [
    ("Python, SQL, PyTorch, Docker", {"Python", "SQL", "PyTorch", "Docker"}),
    ("postgres, Postgre SQL; sklearn; PowerBI", {"PostgreSQL", "scikit-learn", "Power BI"}),
    ("NLP ML DL LLM RAG AWS GCP OCR", {"Natural Language Processing", "Machine Learning", "Deep Learning",
        "Large Language Models", "Retrieval-Augmented Generation", "Amazon Web Services", "Google Cloud Platform", "Optical Character Recognition"}),
    ("Experience in Python, SQL Server and Power BI.", {"Python", "Microsoft SQL Server", "Power BI"}),
    ("SQL Server, SQL Server. Power BI, Power BI.", {"Microsoft SQL Server", "Power BI"}),
    ("SQL and SQL Server; BI and Power BI", {"SQL", "Microsoft SQL Server", "Business Intelligence", "Power BI"}),
    ("BigQuery ML, BigQuery ML", {"BigQuery ML"}),
    ("Prompt Caching and Prompt Caching", {"Prompt Caching"}),
    ("Claude Code and Claude Code", {"Claude Code"}),
    ("C++ C# R&D", {"C++", "C#"}),
    ("C/C++ and R/Python", {"C", "C++", "R", "Python"}),
    ("Go, Python; we go to work", {"Go", "Python"}),
    ("c r go javascript pythons sqlserver", set()),
    ("Send us your CV.", set()),
    ("Experience with CV models and OpenCV", {"Computer Vision"}),
    ("Computer vision experience with OpenCV.", {"Computer Vision"}),
    ("Python Python python", {"Python"}),
    ("PYTHON and Power\tBI", {"Python", "Power BI"}),
    ("Ｐｙｔｈｏｎ", {"Python"}),
    ("Kubernetes and SageMaker", {"Kubernetes", "Amazon SageMaker"}),
    ("ETL / ELT", {"ETL", "ELT"}),
    ("", set()),
])
def test_extraction(extractor, text, expected):
    assert set(extractor.extract(text)) == expected


def test_public_api_and_normalization():
    assert extract_skills("Python") == ["Python"]
    assert normalize_text("Ｐｙｔｈｏｎ") == "Python"
    with pytest.raises(TypeError):
        extract_skills(None)


def test_taxonomy_is_only_vocabulary(tmp_path):
    rows = list(csv.DictReader(DEFAULT_TAXONOMY.open(encoding="utf-8-sig")))
    # OpenCV is absent from the repository taxonomy. Adding it through a custom
    # taxonomy is sufficient; the parser has no parallel vocabulary in code.
    assert not any(r["canonical_name"] == "OpenCV" for r in rows)
    rows.append(dict(skill_id="TEST_OPENCV", canonical_name="OpenCV", abbreviation="", aliases="",
                     skill_group="Vision", observed_count="0"))
    path = tmp_path / "taxonomy.csv"
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=recount_taxonomy.FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    assert set(extract_skills("Computer vision experience with OpenCV.", path)) == {"Computer Vision", "OpenCV"}
    rows.append(dict(rows[-1]))
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=recount_taxonomy.FIELDNAMES)
        writer.writeheader(); writer.writerows(rows)
    with pytest.raises(ValueError, match="bị lặp"):
        SkillExtractor(path)


def test_recount_uses_shared_functions_and_document_fields(extractor):
    assert recount_taxonomy.extract_document_skills is sys.modules["src.parser.skill_extractor"].extract_document_skills
    path = DEFAULT_TAXONOMY.parents[1] / "data/sample/sample_jobs.jsonl"
    jobs = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()]
    updated, evidence = recount_taxonomy.recount(extractor.rows, jobs)
    counts = {r["skill_id"]: 0 for r in extractor.rows}
    by_name = {r["canonical_name"]: r["skill_id"] for r in extractor.rows}
    for job in jobs:
        for name in extractor.extract(document_text(job)):
            counts[by_name[name]] += 1
    assert {r["skill_id"]: int(r["observed_count"]) for r in updated} == counts
    assert len(evidence) == sum(counts.values())
    assert updated == extractor.rows


def test_script_runs_from_other_directory(tmp_path):
    script = DEFAULT_TAXONOMY.parents[1] / "scripts/recount_taxonomy.py"
    result = subprocess.run([sys.executable, str(script), "--check"], cwd=tmp_path, capture_output=True)
    assert result.returncode == 0, result.stderr.decode("utf-8")


@pytest.mark.xfail(strict=True, reason="Matcher hiện chưa xử lý phủ định; ghi trong báo cáo đánh giá.")
def test_negation_known_limitation(extractor):
    assert extractor.extract("Python is not required.") == []


@pytest.mark.xfail(strict=True, reason="Go viết hoa ở đầu câu vẫn có thể khớp tên ngôn ngữ.")
def test_capitalized_go_known_limitation(extractor):
    assert extractor.extract("Go to the office.") == []


@pytest.mark.xfail(strict=True, reason="CV dùng ngữ cảnh toàn tài liệu, chưa tách lời mời gửi hồ sơ.")
def test_mixed_resume_and_vision_context(extractor):
    assert extractor.extract("Send us your CV. Work with OpenCV.") == []
