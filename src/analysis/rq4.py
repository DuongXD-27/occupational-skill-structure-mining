"""RQ4 — giấu title, để thuật toán tự gom nhóm job.

Các bước giải thích trong docs/analysis/rq4_lam_tay.md
Chạy từng bước: python scripts/rq4_tung_buoc.py
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_rand_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    silhouette_score,
)

from . import config


# Kiểm tra dữ liệu

def check_minimum_size(
    n,
    minimum=config.MIN_POSTINGS_FOR_CLUSTERING,
):
    """Kiểm tra đủ số job để clustering."""
    if n < minimum:
        return False, (
            f"RQ4 not run: needs at least {minimum} valid records, "
            f"currently {n}."
        )

    return True, f"RQ4 can run: {n} records (minimum {minimum})."


# Bước 1 — Clustering theo skill

def _fit(X, k, seed):
    """Chia dữ liệu thành k cụm. X chỉ chứa skill, không có title."""
    return KMeans(n_clusters=k, n_init=10, random_state=seed).fit_predict(X)


# Bước 3-5 — Độ ổn định

def compute_stability(
    X,
    k,
    iterations=config.STABILITY_ITERATIONS,
    frac=config.STABILITY_SAMPLE_FRAC,
    seed=config.RANDOM_SEED,
):
    """Khi dữ liệu đổi, các job có còn được xếp chung nhóm không.

    Nhãn cụm là tùy tiện: nhóm máy gọi là 0 lần này có thể là 1 lần sau. So
    theo nhãn sẽ ra 0% dù hai lần chia y hệt nhau.

    Nên không hỏi "job này nhãn mấy", mà hỏi "hai job này có chung nhóm
    không". ARI làm đúng việc đó — nó đếm theo cặp, bỏ qua tên nhãn.
    """
    rng = np.random.default_rng(seed)
    so_tin = len(X)
    co_mau = int(so_tin * frac)

    diem = []

    for _ in range(iterations):
        # bước 3: hai mẫu chồng lấn
        mau_a = rng.choice(so_tin, size=co_mau, replace=False)
        mau_b = rng.choice(so_tin, size=co_mau, replace=False)
        phan_giao = np.intersect1d(mau_a, mau_b)

        if len(phan_giao) < k:
            continue

        # clustering riêng từng mẫu, mỗi lần một seed khởi tạo khác nhau để độ ổn
        # định phản ánh cả dao động do khởi tạo K-Means
        seed_a, seed_b = (int(v) for v in rng.integers(0, 2**31 - 1, size=2))
        nhan_a = pd.Series(_fit(X[mau_a], k, seed_a), index=mau_a)
        nhan_b = pd.Series(_fit(X[mau_b], k, seed_b), index=mau_b)

        # bước 5: chỉ chấm trên phần giao, so theo cặp
        diem.append(
            adjusted_rand_score(nhan_a[phan_giao], nhan_b[phan_giao])
        )

    return float(np.mean(diem)) if diem else np.nan


# Bước 6 — Thử các giá trị k

def run_clustering(
    M,
    k_min=config.K_MIN,
    k_max=config.K_MAX,
    stability_iterations=config.STABILITY_ITERATIONS,
    seed=config.RANDOM_SEED,
):
    """Thử các giá trị k và đánh giá từng k. Title không phải đầu vào ở đây."""
    X = M.values.astype(float)

    rows = []
    nhan_theo_k = {}            # giữ lại để run_rq4 khỏi phải fit lần nữa

    for k in range(k_min, k_max + 1):
        nhan = _fit(X, k, seed)
        nhan_theo_k[k] = nhan

        rows.append({
            "k": k,
            "silhouette": round(
                float(silhouette_score(X, nhan, metric="cosine")), 4
            ),
            "davies_bouldin": round(
                float(davies_bouldin_score(X, nhan)), 4
            ),
            "stability": round(
                compute_stability(X, k, stability_iterations, seed=seed), 4
            ),
        })

    return pd.DataFrame(rows), nhan_theo_k


# Bước 7 — Chọn k

def select_k(
    sweep,
    margin=config.STABILITY_TIE_MARGIN,
    silhouette_margin=config.SILHOUETTE_TIE_MARGIN,
):
    """Chọn k: stability cao nhất, hòa thì xét silhouette, hòa nữa lấy k nhỏ.

    Thứ tự này quan trọng và spec viết chưa rõ. Bỏ vế silhouette thì trên dữ
    liệu gieo sẵn 4 nghề, code chọn k=3: stability bão hòa ở 1.0 cho cả hai,
    còn silhouette tách rõ (0.41 so với 0.54). Leader đã duyệt thứ tự này ngày 2026-11-03.
    """
    cao_nhat = sweep["stability"].max()
    ung_vien = sweep[sweep["stability"] >= cao_nhat - margin]

    sil_cao_nhat = ung_vien["silhouette"].max()
    ung_vien = ung_vien[
        ung_vien["silhouette"] >= sil_cao_nhat - silhouette_margin
    ]

    return int(ung_vien.sort_values("k").iloc[0]["k"])


# Hồ sơ các cụm

def cluster_profiles(M, labels, top=5):
    """Skill phổ biến nhất trong mỗi cụm — đọc TRƯỚC khi ghép title vào."""
    ho_so = M.groupby(labels).mean()

    return pd.DataFrame([
        {
            "cluster": c,
            "n_jobs": int((labels == c).sum()),
            "top_skills": ", ".join(
                ho_so.loc[c].sort_values(ascending=False).head(top).index
            ),
        }
        for c in sorted(ho_so.index)
    ])


# Bước 2 — Sau khi clustering xong mới ghép title

def _with_titles(labels, titles, M):
    """Nhãn cụm và title của các tin CÓ title (tin thiếu title bị bỏ khỏi so sánh)."""
    nghe_that = titles.reindex(M.index)
    co = nghe_that.notna().values
    return np.asarray(labels)[co], nghe_that.values[co]


def unblind(labels, titles, M):
    """Ghép title vào các cụm — chỉ đến lúc này, và chỉ để diễn giải."""
    nhan, nghe = _with_titles(labels, titles, M)
    df = pd.DataFrame({"cluster": nhan, "title": nghe})

    return (
        df.groupby("cluster")["title"]
        .apply(lambda s: ", ".join(s.value_counts().head(3).index))
        .reset_index(name="titles_after_unblinding")
    )


def compare_to_titles(labels, titles, M):
    """Con số chính của cả đồ án.

    Gần 1: dữ liệu tái tạo lại đúng các title đang dùng.
    Gần 0: tên nghề và công việc thật đã lệch nhau.
    """
    nhan, nghe_that = _with_titles(labels, titles, M)
    if len(nghe_that) == 0:
        raise ValueError("no posting has a title; cannot compare clusters to titles")
    labels = nhan

    return {
        "ari": round(float(adjusted_rand_score(nghe_that, labels)), 4),
        "nmi": round(
            float(normalized_mutual_info_score(nghe_that, labels)), 4
        ),
        "n_compared": int(len(nghe_that)),
    }


def cluster_title_crosstab(labels, titles, M):
    """Bảng chéo cụm × title (số tin). Chỉ gọi SAU khi nhãn cụm đã chốt."""
    nhan, nghe = _with_titles(labels, titles, M)
    return pd.crosstab(pd.Series(nghe, name="title"), pd.Series(nhan, name="cluster"))


def cluster_examples(M, labels, titles=None, n=3):
    """Mỗi cụm `n` tin gần tâm cụm nhất (cosine) — để người đọc thấy cụm là gì."""
    X = M.values.astype(float)
    labels = np.asarray(labels)
    norm = np.linalg.norm(X, axis=1)
    rows = []
    for c in sorted(set(labels)):
        idx = np.where(labels == c)[0]
        tam = X[idx].mean(axis=0)
        cos = X[idx] @ tam / np.where(norm[idx] * np.linalg.norm(tam) == 0, 1, norm[idx] * np.linalg.norm(tam))
        for rank, i in enumerate(idx[np.argsort(-cos)][:n], 1):
            jid = M.index[i]
            rows.append({
                "cluster": int(c), "rank": rank, "job_id": jid,
                "title": None if titles is None else titles.get(jid),
                "cosine_to_centroid": round(float(cos[list(idx).index(i)]), 4),
                "skills": ", ".join(M.columns[X[i] > 0]),
            })
    return pd.DataFrame(rows)


# Phân cụm phân cấp — phương pháp đối chứng cho K-Means (phạm vi bắt buộc §11)

def hierarchical_labels(M, k,
                        metric=config.HIERARCHICAL_METRIC,
                        method=config.HIERARCHICAL_LINKAGE):
    """Cắt cây phân cấp thành k cụm. Nhãn 0..k-1, cùng quy ước với K-Means.

    Khoảng cách Jaccard hợp với vector skill nhị phân hơn Euclid (hai tin cùng
    THIẾU một skill không làm chúng giống nhau). Title không phải đầu vào.
    """
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial.distance import pdist

    X = M.values.astype(bool)
    Z = linkage(pdist(X, metric=metric), method=method)
    nhan = fcluster(Z, t=k, criterion="maxclust")
    _, nhan = np.unique(nhan, return_inverse=True)
    return nhan


def _diem_noi_tai(X, nhan):
    """Silhouette (cosine) và Davies-Bouldin; None khi chỉ có 1 cụm."""
    if len(set(nhan)) < 2:
        return None, None
    return (round(float(silhouette_score(X, nhan, metric="cosine")), 4),
            round(float(davies_bouldin_score(X, nhan)), 4))


def compare_methods(M, kmeans_labels, hier_labels, titles=None):
    """Bảng so sánh K-Means với phân cấp ở cùng k.

    Ngoài điểm nội tại còn ghi cỡ cụm lớn nhất: liên kết average hay tạo một cụm
    khổng lồ cộng vài cụm lẻ, silhouette vẫn đẹp nhưng cấu trúc vô dụng.
    """
    X = M.values.astype(float)
    rows = []
    for ten, nhan in (("kmeans", kmeans_labels), ("hierarchical", hier_labels)):
        nhan = np.asarray(nhan)
        sil, db = _diem_noi_tai(X, nhan)
        co = pd.Series(nhan).value_counts()
        row = {
            "method": ten,
            "k": int(len(co)),
            "silhouette": sil,
            "davies_bouldin": db,
            "largest_cluster_share": round(float(co.max() / len(nhan)), 4),
            "singleton_clusters": int((co == 1).sum()),
        }
        if titles is not None:
            row.update({f"{m}_vs_titles": v for m, v in compare_to_titles(nhan, titles, M).items()
                        if m != "n_compared"})
        rows.append(row)
    bang = pd.DataFrame(rows)
    giong_nhau = {
        "ari_between_methods": round(float(adjusted_rand_score(kmeans_labels, hier_labels)), 4),
        "nmi_between_methods": round(float(normalized_mutual_info_score(kmeans_labels, hier_labels)), 4),
    }
    return bang, giong_nhau


# PCA chỉ để trực quan hóa

def pca_coordinates(M, labels):
    """Giảm xuống 2 chiều để vẽ. PCA không bao giờ là đầu vào của clustering."""
    xy = PCA(
        n_components=2,
        random_state=config.RANDOM_SEED,
    ).fit_transform(M.values.astype(float))

    return pd.DataFrame({
        "job_id": M.index,
        "x": xy[:, 0],
        "y": xy[:, 1],
        "cluster": labels,
    })


# Chạy toàn bộ RQ4 — thứ tự các dòng chính là luật chống gian lận

def run_rq4(
    M,
    titles=None,
    stability_iterations=config.STABILITY_ITERATIONS,
):
    """Chạy toàn bộ RQ4. Đảo thứ tự các bước dưới là hỏng cả kết quả."""
    ok, message = check_minimum_size(len(M))

    if not ok:
        return {"status": "skipped", "message": message}

    sweep, nhan_theo_k = run_clustering(         # title chưa xuất hiện
        M,
        stability_iterations=stability_iterations,
    )

    k = select_k(sweep)                          # vẫn chưa

    labels = nhan_theo_k[k]                      # cụm chốt tại đây
    hier = hierarchical_labels(M, k)             # đối chứng, cùng k, vẫn chưa thấy title

    result = {
        "status": "ok",
        "message": message,
        "sweep": sweep,
        "chosen_k": k,
        # lấy thẳng từ sweep — không tính lại thứ đã có
        "scores": sweep.loc[sweep["k"] == k,
                            ["silhouette", "davies_bouldin"]].iloc[0].to_dict(),
        "profiles": cluster_profiles(M, labels),
        "pca": pca_coordinates(M, labels),
        "labels": pd.Series(labels, index=M.index, name="cluster"),
        "hierarchical_labels": pd.Series(hier, index=M.index, name="cluster_hierarchical"),
    }

    # mọi thứ phía trên đã tính xong khi title còn bị giấu
    if titles is not None:
        result["unblinded"] = unblind(labels, titles, M)
        result["agreement"] = compare_to_titles(labels, titles, M)
        result["crosstab"] = cluster_title_crosstab(labels, titles, M)
    result["examples"] = cluster_examples(M, labels, titles)

    result["method_comparison"], result["method_agreement"] = compare_methods(
        M, labels, hier, titles)

    return result
