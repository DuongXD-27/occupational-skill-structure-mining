"""Các bảng/hình bổ sung theo analysis_spec §4–§6 và 8 kiểm tra chất lượng §9."""
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import adjusted_rand_score

from src.analysis import config, quality, report, rq2, rq3, rq4, synthetic


@pytest.fixture(scope="module")
def data():
    df = synthetic.generate_jobs(n=400)
    return df, synthetic.build_matrix(df)


# --- RQ2 ---------------------------------------------------------------

def test_negative_pairs_are_below_chance_and_well_supported(data):
    _, M = data
    neg = rq2.negative_pairs(M)
    assert len(neg) > 0
    assert (neg["lift"] < 1).all()
    assert (neg["expected"] >= config.MIN_COOCCURRENCE).all()
    # dữ liệu gieo 4 nghề: cặp "tránh nhau" mạnh nhất phải là skill của hai nghề khác nhau
    family = {s: f for f, spec in synthetic.FAMILIES.items() for s in spec["core"]}
    for a, b in zip(neg["skill_a"].head(10), neg["skill_b"].head(10)):
        assert family.get(a) != family.get(b) or family.get(a) is None


def test_negative_pairs_ignore_pairs_that_are_merely_rare():
    M = pd.DataFrame({"a": [1] * 50 + [0] * 50, "b": [0] * 98 + [1] * 2})
    assert rq2.negative_pairs(M).empty     # kỳ vọng 1 lần < 5: hiếm, không phải "tránh nhau"


def test_top_pairs_has_each_metric(data):
    _, M = data
    top = rq2.top_pairs_by_metric(rq2.compute_associations(M))
    assert set(top["metric"]) == {"lift", "npmi", "jaccard"}
    assert top.groupby("metric").size().max() <= config.TOP_PAIRS_PER_METRIC
    first = top[top["metric"] == "npmi"].iloc[0]
    assert first["rank"] == 1 and first["value"] == top[top["metric"] == "npmi"]["value"].max()


# --- RQ3 ---------------------------------------------------------------

def test_flagged_pairs_use_three_levels():
    sim = pd.DataFrame({"title_a": list("abcd"), "title_b": list("wxyz"),
                        "cosine": [0.95, 0.85, 0.72, 0.5]})
    out = rq3.flag_title_pairs(sim)
    assert list(out["level"]) == [0.9, 0.8, 0.7]


def test_title_profiles_report_shares_for_qualifying_titles(data):
    df, M = data
    titles = df.set_index("job_id")["normalized_job_title"]
    prof = rq3.title_profiles(M, titles)
    assert (prof["n_postings"] >= config.MIN_POSTINGS_PER_TITLE).all()
    assert prof["share"].between(0, 1).all()
    de = prof[(prof["title"] == "Data Engineer") & (prof["rank"] <= 5)]["skill"]
    assert {"Spark", "Airflow", "Kafka"} & set(de)


def test_baseline_has_both_ends(data):
    df, M = data
    out = rq3.run_rq3(M, df.set_index("job_id")["normalized_job_title"], iterations=50)
    d = out["dispersion"]
    assert (d["baseline_p5"] <= d["baseline_mean"]).all() and (d["baseline_mean"] <= d["baseline_p95"]).all()


# --- RQ4 ---------------------------------------------------------------

def test_hierarchical_finds_the_same_structure(data):
    df, M = data
    hier = rq4.hierarchical_labels(M, 4)
    assert len(set(hier)) == 4 and set(hier) == {0, 1, 2, 3}
    assert adjusted_rand_score(df.set_index("job_id").loc[M.index, "true_family"], hier) > 0.7


def test_rq4_reports_method_comparison(data):
    df, M = data
    out = rq4.run_rq4(M, titles=df.set_index("job_id")["normalized_job_title"], stability_iterations=5)
    cmp = out["method_comparison"]
    assert list(cmp["method"]) == ["kmeans", "hierarchical"]
    assert {"silhouette", "largest_cluster_share", "ari_vs_titles"} <= set(cmp.columns)
    assert 0 <= out["method_agreement"]["ari_between_methods"] <= 1


def test_hierarchical_never_sees_titles(data):
    """Nhãn phân cấp chỉ phụ thuộc M: đổi title không đổi nhãn."""
    df, M = data
    a = rq4.run_rq4(M, titles=df.set_index("job_id")["normalized_job_title"], stability_iterations=3)
    b = rq4.run_rq4(M, titles=None, stability_iterations=3)
    assert a["hierarchical_labels"].equals(b["hierarchical_labels"])


# --- báo cáo ghi đủ file -----------------------------------------------

def test_write_analysis_writes_new_artifacts(data, tmp_path):
    df, M = data
    status = report.write_analysis(M, df.set_index("job_id")["normalized_job_title"], tmp_path,
                                   log=lambda *_: None, stability_iterations=3)
    for name in ("rq2_negative_pairs.csv", "rq2_top_pairs_by_metric.csv", "rq2_top_skills.png",
                 "rq2_association_heatmap.png", "rq2_cooccurrence_network.png"):
        assert name in status["RQ2"]["artifacts"]
    for name in ("rq3_title_profiles.csv", "rq3_flagged_pairs.csv", "rq3_dispersion_vs_baseline.png",
                 "rq3_title_dendrogram.png", "rq3_title_similarity.png", "rq3_title_profiles.png"):
        assert name in status["RQ3"]["artifacts"]
    for name in ("rq4_method_comparison.csv", "rq4_method_agreement.csv", "rq4_cluster_examples.csv",
                 "rq4_cluster_title_crosstab.csv", "rq4_cluster_title_heatmap.png"):
        assert name in status["RQ4"]["artifacts"]
    for rq in status.values():
        for a in rq["artifacts"]:
            assert (tmp_path / a).stat().st_size > 0


# --- 8 kiểm tra chất lượng ---------------------------------------------

def _tables(n=40, skills_per_job=4, text_len=600):
    rng = np.random.default_rng(0)
    clean = pd.DataFrame({
        "job_id": [f"j{i}" for i in range(n)],
        "company": [f"c{i % 7}" for i in range(n)],
        "normalized_job_title": ["Data Engineer" if i % 2 else "Data Analyst" for i in range(n)],
        "job_description": ["x" * text_len + str(i) for i in range(n)],
        "job_requirements": ["y" for _ in range(n)],
        "relevance_flag": True, "duplicate_flag": False,
    })
    pool = [f"S{k}" for k in range(30)]
    skills = pd.DataFrame({
        "job_id": clean["job_id"],
        "extracted_skills": [list(rng.choice(pool, skills_per_job, replace=False)) for _ in range(n)],
    })
    skills["skill_count"] = skills["extracted_skills"].map(len)
    return clean, skills


def test_quality_checks_are_eight_and_pass_on_good_data():
    checks = quality.run_checks(*_tables())
    assert list(checks["check"]) == [f"QC{i}" for i in range(1, 9)]
    assert checks["passed"].all(), quality.failed(checks)


def test_quality_catches_a_weak_extractor():
    clean, skills = _tables(skills_per_job=1)
    failed = quality.failed(quality.run_checks(clean, skills))
    assert any(f.startswith("QC3") for f in failed)


def test_quality_catches_null_skills_and_missing_rows():
    clean, skills = _tables()
    skills.loc[0, "extracted_skills"] = None
    skills = skills.iloc[:-1]
    failed = {f.split()[0] for f in quality.failed(quality.run_checks(clean, skills))}
    assert {"QC1", "QC2"} <= failed


def test_quality_catches_residual_duplicates_and_short_text():
    clean, skills = _tables(text_len=50)
    clean.loc[1:5, ["company", "normalized_job_title", "job_description"]] = clean.loc[0, [
        "company", "normalized_job_title", "job_description"]].values
    failed = {f.split()[0] for f in quality.failed(quality.run_checks(clean, skills))}
    assert {"QC6", "QC7"} <= failed


def test_quality_catches_a_skill_in_every_posting_and_missing_titles():
    clean, skills = _tables()
    skills["extracted_skills"] = skills["extracted_skills"].map(lambda l: l + ["Communication"])
    clean.loc[3, "normalized_job_title"] = ""
    failed = {f.split()[0] for f in quality.failed(quality.run_checks(clean, skills))}
    assert {"QC5", "QC8"} <= failed


def test_quality_ignores_invalid_records():
    clean, skills = _tables()
    extra = clean.iloc[[0]].assign(job_id="bad", relevance_flag=False, job_description="")
    checks = quality.run_checks(pd.concat([clean, extra]), skills)
    assert checks["passed"].all()


def test_crosstab_counts_every_titled_posting(data):
    df, M = data
    titles = df.set_index("job_id")["normalized_job_title"]
    out = rq4.run_rq4(M, titles=titles, stability_iterations=3)
    assert out["crosstab"].values.sum() == out["agreement"]["n_compared"]
    ex = out["examples"]
    assert set(ex["cluster"]) == set(out["labels"])
    assert ex.groupby("cluster").size().max() <= 3
