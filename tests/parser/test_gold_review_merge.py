"""Gộp kết quả trang duyệt gold: đúng định dạng gold, tính kappa, ghi xung đột."""
import json

from scripts import merge_gold_reviews as m
from tools.gold_review.build import build_data
from src.parser.evaluation import evaluate_file

DATA = build_data()
JOB = next(j for j in DATA["jobs"] if j["kp"] and any(s["k"] == "missing" for s in j["S"]))
MISS = next(i for i, s in enumerate(JOB["S"]) if s["k"] == "missing")


def _doc(**kw):
    d = {"v": 1, "rej": {}, "res": {}, "added": [], "ind": [], "indDone": True, "note": "", "done": True}
    d.update(kw)
    return d


def _resolve_all(choice_label="keep"):
    return {str(i): ("add" if s["k"] == "missing" else choice_label) for i, s in enumerate(JOB["S"])}


def test_final_annotations_follow_decisions():
    keep_all = m.final_annotations(JOB, _doc(res=_resolve_all()))
    ids = {a["id"] for a in keep_all}
    assert JOB["S"][MISS]["id"] in ids                      # gợi ý thiếu được thêm
    dropped = m.final_annotations(JOB, _doc(res=_resolve_all(), rej={"0": True}))
    plain0 = all(s.get("li") != 0 for s in JOB["S"] if s["k"] == "label")
    assert (len(dropped) == len(keep_all) - 1) == plain0     # bỏ nhãn 0 chỉ có tác dụng khi nhãn đó không bị góp ý


def test_merge_writes_valid_gold_and_conflicts(tmp_path):
    a_ind = [{"n": "Redis", "id": "SK0268", "s": 0, "e": 1}]
    b_ind = [{"n": "Redis", "id": "SK0268", "s": 0, "e": 1}, {"n": "Python", "id": "SK0256", "s": 0, "e": 1}]
    res_a = _resolve_all()
    res_b = dict(res_a, **{str(MISS): "skip"})
    reviews = {"Dương": {JOB["id"]: _doc(res=res_a, ind=a_ind)}, "Cường": {JOB["id"]: _doc(res=res_b, ind=b_ind)}}
    rows, conflicts, summary = m.merge(reviews)
    assert summary["jobs_reviewed"] == 1 and summary["kappa"][0]["jobs"] == 1
    assert summary["kappa"][0]["positive_agreement"] == round(2 / 3, 4)
    assert any(c["skill_id"] == JOB["S"][MISS]["id"] for c in conflicts)
    rows_pref, _, _ = m.merge(reviews, prefer="cuong")
    assert JOB["S"][MISS]["n"] not in rows_pref[0]["gold_skills"] and JOB["S"][MISS]["n"] in rows[0]["gold_skills"]
    gold = tmp_path / "gold.jsonl"
    gold.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    report = evaluate_file(gold, tmp_path / "out", "taxonomy/skills_taxonomy.csv", "data/sample/sample_jobs.jsonl")
    assert report["human_reviewed"] is True and report["jobs"] == 1


def test_slug_handles_vietnamese():
    assert m.slug("Hoàng Quốc Cường") == "hoang-quoc-cuong"
    assert m.slug("Nguyễn Tuấn Dương") == "nguyen-tuan-duong"


def test_api_design_added_without_reviewer_decision():
    """Quy ước 05/11: góp ý thiếu API Design được thêm luôn, kể cả khi người duyệt chọn bỏ qua."""
    autos = [(j, i) for j in DATA["jobs"] for i, s in enumerate(j["S"]) if s.get("auto")]
    assert len(autos) == 12
    assert all(j["S"][i]["n"] == "API Design" and j["S"][i]["auto"] == "add" for j, i in autos)
    job, si = autos[0]
    for res in ({}, {str(si): "skip"}):
        ann = m.final_annotations(job, _doc(res=res))
        assert any(a["n"] == "API Design" for a in ann)
