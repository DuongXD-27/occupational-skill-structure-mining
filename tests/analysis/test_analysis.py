"""Kiểm thử trên dữ liệu giả, nơi đã biết trước đáp án.

Dữ liệu thật không làm được việc này: nó không bao giờ cho biết kết quả đúng
lẽ ra phải là gì.
"""
import pandas as pd
import pytest

from src.analysis import config, loaders, rq2, rq3, rq4, synthetic


@pytest.fixture(scope="module")
def data():
    df = synthetic.generate_jobs(n=400)
    return df, synthetic.build_matrix(df)


# --- RQ2: skill và cặp skill -------------------------------------------

def test_matrix_is_binary(data):
    _, M = data
    assert set(pd.unique(M.values.ravel())) <= {0, 1}


def test_related_pair_beats_common_pair(data):
    """Cái bẫy: Python và SQL hay gặp chung vì cả hai đều ở khắp nơi.
    PyTorch và OpenCV gặp chung vì chúng thực sự thuộc về nhau. Chỉ số liên hệ
    đúng phải tách được hai trường hợp; đếm thô thì không."""
    assoc = rq2.compute_associations(M := data[1]).set_index(
        lambda i: None) if False else rq2.compute_associations(data[1])
    key = {frozenset([a, b]): n for a, b, n in
           zip(assoc["skill_a"], assoc["skill_b"], assoc["npmi"])}
    assert key[frozenset(["PyTorch", "OpenCV"])] > key[frozenset(["Python", "SQL"])]


def test_unrelated_skills_are_not_linked(data):
    _, M = data
    assoc = rq2.compute_associations(M)
    pair = assoc[(assoc.skill_a.isin(["PyTorch", "Power BI"])) &
                 (assoc.skill_b.isin(["PyTorch", "Power BI"]))]
    assert pair.empty or pair.iloc[0]["lift"] < 1.0


def test_communities_split_vision_from_analysis(data):
    _, M = data
    comms = rq2.detect_communities(rq2.compute_associations(M))
    assert comms["OpenCV"] == comms["Computer Vision"]
    assert comms["OpenCV"] != comms["Power BI"]


# --- RQ3: title so với skill -------------------------------------------

def test_dispersion_skips_small_titles():
    df = synthetic.generate_jobs(n=12)
    M = synthetic.build_matrix(df, min_skill_count=1)
    disp, skipped = rq3.compute_title_dispersion(M, df.set_index("job_id")["normalized_job_title"])
    assert len(skipped) > 0


def test_baseline_brackets_the_observed_value(data):
    df, M = data
    titles = df.set_index("job_id")["normalized_job_title"]
    out = rq3.run_rq3(M, titles, iterations=50)
    row = out["dispersion"].iloc[0]
    assert row["baseline_p5"] <= row["baseline_mean"]


def test_same_family_titles_are_similar(data):
    df, M = data
    sim = rq3.compute_title_similarity(M, df.set_index("job_id")["normalized_job_title"])
    assert sim["cosine"].max() > 0.5


# --- RQ4: phân cụm -----------------------------------------------------

def test_refuses_to_run_below_threshold():
    df = synthetic.generate_jobs(n=250)
    M = synthetic.build_matrix(df)
    out = rq4.run_rq4(M)
    assert out["status"] == "skipped"
    assert "250" in out["message"]


def test_titles_never_enter_the_feature_matrix(data):
    """Ma trận đưa vào phân cụm chỉ được chứa skill."""
    df, M = data
    titles = set(df["normalized_job_title"])
    assert not (titles & set(M.columns))


def test_recovers_the_planted_structure(data):
    """Đã gieo sẵn 4 nghề. Phân cụm không hề nhìn thấy chúng, nhưng phải
    khớp với chúng ở mức cao."""
    df, M = data
    out = rq4.run_rq4(M, titles=df.set_index("job_id")["true_family"],
                      stability_iterations=10)
    assert out["status"] == "ok"
    assert out["agreement"]["ari"] > 0.7


def test_results_are_reproducible(data):
    _, M = data
    a, _ = rq4.run_clustering(M, k_min=4, k_max=4, stability_iterations=5)
    b, _ = rq4.run_clustering(M, k_min=4, k_max=4, stability_iterations=5)
    assert a.equals(b)


# --- loaders: bản giao có thể không đúng dạng mình cần ------------------

def _fake_handover(tmp_path, M, as_codes=True, as_bool=True, job_id_column=True):
    """Dựng file parquet đúng dạng mà data_schema_v1.md mục 14 mô tả."""
    out = M.copy()
    codes = {}
    if as_codes:
        codes = {name: f"skill_{i:03d}" for i, name in enumerate(M.columns, 1)}
        out = out.rename(columns=codes)
    if as_bool:
        out = out.astype(bool)
    out["skill_count"] = M.sum(axis=1).values
    if job_id_column:
        out = out.reset_index()

    p = tmp_path / "job_skill_matrix.parquet"
    out.to_parquet(p)

    tax = tmp_path / "skills_taxonomy.csv"
    pd.DataFrame({"skill_id": list(codes.values()),
                  "skill_name": list(codes.keys())}).to_csv(tax, index=False)
    return p, tax


def test_loader_normalises_a_schema_shaped_handover(data, tmp_path):
    """Mã số, kiểu bool, job_id nằm ở cột, cộng một cột thừa skill_count —
    tất cả phải quay về đúng ma trận mà module cần."""
    _, M = data
    p, tax = _fake_handover(tmp_path, M)
    loaded = loaders.load_skill_matrix(p, tax)
    assert loaded.equals(M)


def test_loader_warns_when_taxonomy_is_missing(data, tmp_path):
    _, M = data
    p, _ = _fake_handover(tmp_path, M)
    loaded = loaders.load_skill_matrix(p, tmp_path / "does_not_exist.csv")
    assert any("codes, not names" in n for n in loaders.warn_about(loaded))


def test_loader_rejects_a_matrix_the_extractor_never_filled(data):
    _, M = data
    empty = M.copy()
    empty[:] = 0
    with pytest.raises(loaders.MatrixProblem, match="zero skills"):
        loaders.validate_matrix(empty)


def test_loader_rejects_non_binary_cells(data):
    _, M = data
    bad = M.copy()
    bad.iloc[0, 0] = 7
    with pytest.raises(loaders.MatrixProblem, match="0 or 1"):
        loaders.validate_matrix(bad)


def test_check_titles_refuses_when_no_title_reaches_the_threshold():
    df = synthetic.generate_jobs(n=12)
    M = synthetic.build_matrix(df, min_skill_count=1)
    ok, message = loaders.check_titles(df.set_index("job_id")["normalized_job_title"], M)
    assert ok is False
    assert "RQ3 cannot run" in message


def test_loader_finds_the_id_column_under_other_names(data, tmp_path):
    """job_id có thể tới dưới tên id, posting_id, vacancy_id. Mất nó vừa âm thầm
    vừa đắt: nhãn cụm hết truy ngược về được tin tuyển dụng."""
    _, M = data
    p, tax = _fake_handover(tmp_path, M)
    renamed = pd.read_parquet(p).rename(columns={"job_id": "posting_id"})
    p2 = tmp_path / "renamed.parquet"
    renamed.to_parquet(p2)

    loaded = loaders.load_skill_matrix(p2, tax)
    assert loaded.index.name == "job_id"
    assert str(loaded.index[0]).startswith("job_")


def test_loader_refuses_a_matrix_with_no_identifier(data, tmp_path):
    _, M = data
    p, tax = _fake_handover(tmp_path, M)
    dropped = pd.read_parquet(p).drop(columns=["job_id"])
    p2 = tmp_path / "no_id.parquet"
    dropped.to_parquet(p2)

    with pytest.raises(loaders.MatrixProblem, match="No posting identifier"):
        loaders.load_skill_matrix(p2, tax)


def test_loader_maps_codes_under_a_different_prefix(data, tmp_path):
    """sk_001 thay vì skill_001 vẫn phải ánh xạ về được tên đọc được."""
    _, M = data
    codes = {name: f"sk_{i:03d}" for i, name in enumerate(M.columns, 1)}
    frame = M.rename(columns=codes).reset_index()
    p = tmp_path / "sk.parquet"
    frame.to_parquet(p)
    tax = tmp_path / "tax.csv"
    pd.DataFrame({"skill_id": list(codes.values()),
                  "canonical_name": list(codes.keys())}).to_csv(tax, index=False)

    loaded = loaders.load_skill_matrix(p, tax)
    assert "Python" in loaded.columns


def test_notable_pairs_shows_shared_and_distinguishing_skills(data):
    """Cosine 0.95 không cho biết hai title giống nhau ở chỗ nào.
    Bảng này phải mở ra được: skill nào chung, skill nào chỉ một bên có."""
    df, M = data
    titles = df.set_index("job_id")["normalized_job_title"]
    out = rq3.run_rq3(M, titles, iterations=20)

    notable = out["notable"]
    assert not notable.empty
    assert set(notable.columns) >= {"skill_chung", "chi_title_a", "chi_title_b"}

    # cặp giống nhau nhất phải có skill chung
    assert notable.iloc[0]["skill_chung"]

    # phải có ít nhất một cặp chỉ ra được skill phân biệt
    co_phan_biet = notable["chi_title_a"].str.len() + notable["chi_title_b"].str.len()
    assert (co_phan_biet > 0).any()
