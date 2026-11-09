import json

import pandas as pd
import pytest

from scripts import merge_role_labels as m
from scripts.sample_role_labeling import sample


def _clean(n_kept=40, n_excl=10, n_dup=3):
    rows = []
    for i in range(n_kept + n_excl + n_dup):
        rows.append({"job_id": f"j{i:03d}", "job_text": "text",
                     "relevance_flag": i < n_kept or i >= n_kept + n_excl,
                     "duplicate_flag": i >= n_kept + n_excl})
    return pd.DataFrame(rows)


def test_sample_keeps_all_excluded_drops_duplicates_and_is_deterministic():
    s = sample(_clean(), n=30, k=6, batches=4)
    assert len(s) == 30 and s["job_id"].is_unique
    assert (s["stratum"] == "excluded").sum() == 10
    assert not s["job_id"].isin([f"j{i:03d}" for i in range(50, 53)]).any()
    assert (s["batch"] == "K").sum() == 6
    assert set(s["batch"]) == {"K", "B1", "B2", "B3", "B4"}
    pd.testing.assert_frame_equal(s, sample(_clean().sample(frac=1, random_state=1), n=30, k=6, batches=4))


def test_sample_rejects_impossible_size():
    with pytest.raises(ValueError):
        sample(_clean(), n=100)


def test_kappa_examples():
    assert m.cohen_kappa(["DA", "DE", "DS"], ["DA", "DE", "DS"]) == 1.0
    # đồng ý 2/4, p_e = 0,5 → kappa 0; đồng ý 3/4, p_e = 0,5 → kappa 0,5
    assert m.cohen_kappa(["DA", "DA", "DE", "DE"], ["DA", "DE", "DE", "DA"]) == pytest.approx(0.0)
    assert m.cohen_kappa(["DA", "DA", "DE", "DE"], ["DA", "DA", "DE", "DA"]) == pytest.approx(0.5)


def _doc(name, labels):
    return {"format": "role-labels-v1", "labeler": name,
            "labels": [{"job_id": j, "batch": b, "primary": p, "secondary": s, "unsure": False, "note": ""}
                       for j, b, p, s in labels]}


def test_merge_agreement_conflict_and_adjudication(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps(_doc("Duong", [("x1", "K", "DA", ""), ("x2", "K", "MLE", "DS"), ("x3", "B1", "DE", "")])))
    (tmp_path / "b.json").write_text(json.dumps(_doc("Cuong", [("x1", "K", "DA", ""), ("x2", "K", "DS", "")])))
    reviews = m.load_reviews(str(tmp_path / "*.json"))
    labels, conflicts, summary = m.merge(reviews)
    st = labels.set_index("job_id")["status"].to_dict()
    assert st == {"x1": "agreed", "x2": "conflict", "x3": "single"}
    assert list(conflicts["job_id"]) == ["x2"] and conflicts.iloc[0]["Duong"] == "MLE+DS"
    assert summary["pairwise_kappa"][0]["shared"] == 2
    assert summary["most_confused"] == [{"roles": ["DS", "MLE"], "n": 1}]
    adj = pd.DataFrame([{"job_id": "x2", "primary": "MLE", "secondary": "DS", "reason": "họp 10/11"}])
    labels2, _, _ = m.merge(reviews, adj)
    r = labels2.set_index("job_id").loc["x2"]
    assert (r["primary"], r["status"]) == ("MLE", "adjudicated")


def test_load_rejects_unknown_role(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps(_doc("X", [("x1", "K", "DATA", "")])))
    with pytest.raises(ValueError):
        m.load_reviews(str(tmp_path / "*.json"))
