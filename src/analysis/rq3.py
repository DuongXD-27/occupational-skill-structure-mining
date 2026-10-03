"""RQ3 — tên công việc có nói đúng công việc không?
"""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from . import config


# Bước 1-2 — Độ giống nhau giữa hai tin

def _mean_pairwise_jaccard(X):
    """Jaccard trung bình trên mọi cặp tin trong nhóm (vector hóa bằng X @ X.T)."""
    if len(X) < 2:
        return np.nan

    so_skill_chung = X @ X.T
    so_skill_moi_tin = X.sum(axis=1)

    so_skill_it_nhat_mot = (
        so_skill_moi_tin[:, None]
        + so_skill_moi_tin[None, :]
        - so_skill_chung
    )

    with np.errstate(divide="ignore", invalid="ignore"):
        jaccard = np.where(
            so_skill_it_nhat_mot > 0,
            so_skill_chung / so_skill_it_nhat_mot,
            0.0,
        )

    nua_tren = np.triu_indices(len(X), k=1)
    return float(jaccard[nua_tren].mean())


# Bước 3-4 — Độ phân tán của từng title

def compute_title_dispersion(M, titles,
                             min_postings=config.MIN_POSTINGS_PER_TITLE):
    """dispersion = 1 − jaccard trung bình trong title. Cao = cái tên nói lên ít.

    Title dưới ngưỡng trả về ở bảng `skipped`, không âm thầm loại đi.
    """
    rows = []
    skipped = []

    for title, nhom in M.groupby(titles.reindex(M.index).values):
        if len(nhom) < min_postings:
            skipped.append({"title": title, "n_postings": len(nhom)})
            continue

        jaccard_tb = _mean_pairwise_jaccard(nhom.values.astype(float))

        rows.append({
            "title": title,
            "n_postings": len(nhom),
            "dispersion": round(1 - jaccard_tb, 4),
        })

    disp = pd.DataFrame(rows, columns=["title", "n_postings", "dispersion"])

    return (
        disp.sort_values("dispersion", ascending=False).reset_index(drop=True),
        pd.DataFrame(skipped, columns=["title", "n_postings"]),
    )


# Bước 6 — Mốc so sánh: nhóm bốc ngẫu nhiên

def bootstrap_baseline(M, group_size,
                       iterations=config.BOOTSTRAP_ITERATIONS,
                       seed=config.RANDOM_SEED):
    """Độ phân tán của một nhóm bốc ngẫu nhiên.

    Mốc phải CÙNG CỠ với nhóm của title: nhóm nhỏ luôn nhiễu hơn, so với mốc
    khác cỡ là tự tạo ra kết quả giả.
    """
    rng = np.random.default_rng(seed)
    X = M.values.astype(float)

    phan_tan = []
    for _ in range(iterations):
        nhom_boc_dai = rng.choice(len(X), size=group_size, replace=False)
        phan_tan.append(1 - _mean_pairwise_jaccard(X[nhom_boc_dai]))

    return {
        "group_size": group_size,
        "mean": round(float(np.mean(phan_tan)), 4),
        "p5": round(float(np.percentile(phan_tan, 5)), 4),
        "p95": round(float(np.percentile(phan_tan, 95)), 4),
    }


# Bước 7 — So title với mốc

def add_baselines(dispersion, M, iterations=config.BOOTSTRAP_ITERATIONS):
    """informative=False: title rơi vào vùng ngẫu nhiên, cái tên không mang
    nhiều thông tin hơn một nhãn dán bừa."""
    out = dispersion.copy()

    moc = {
        n: bootstrap_baseline(M, n, iterations)
        for n in out["n_postings"].unique()
    }

    out["baseline_mean"] = out["n_postings"].map(lambda n: moc[n]["mean"])
    out["baseline_p5"] = out["n_postings"].map(lambda n: moc[n]["p5"])
    out["informative"] = out["dispersion"] < out["baseline_p5"]

    return out


# Bước 8-10 — Title khác nhau, skill có giống nhau không
#
# Chiều 1 so TIN với TIN. Chiều này so TITLE với TITLE: một title là một NHÓM
# tin nên phải nén mỗi nhóm thành một dãy số trước khi so.

def compute_title_similarity(M, titles,
                             min_postings=config.MIN_POSTINGS_PER_TITLE):
    """Hồ sơ title = tỉ lệ tin trong title đó có từng skill (DA có 3 tin, 2 tin
    đòi Excel -> cột Excel = 0.67). cosine 1 = cùng việc hai tên, 0 = khác hẳn.
    """
    ho_so = M.groupby(titles.reindex(M.index).values).mean()
    so_tin = titles.reindex(M.index).value_counts()

    du_nguong = [t for t in ho_so.index if so_tin.get(t, 0) >= min_postings]
    ho_so = ho_so.loc[du_nguong]

    if len(ho_so) < 2:
        return pd.DataFrame(columns=["title_a", "title_b", "cosine"])

    S = cosine_similarity(ho_so.values)

    rows = [
        {
            "title_a": ho_so.index[i],
            "title_b": ho_so.index[j],
            "cosine": round(float(S[i, j]), 4),
        }
        for i in range(len(ho_so))
        for j in range(i + 1, len(ho_so))
    ]

    return pd.DataFrame(rows).sort_values(
        "cosine", ascending=False
    ).reset_index(drop=True)


# Bảng minh họa — các cặp title đáng chú ý

def notable_title_pairs(M, titles, similarity, top=5, nguong=0.5):
    """Mở ra con số cosine: skill nào cả hai cùng đòi, skill nào chỉ một bên.

    Một skill tính là "title này có đòi" khi từ `nguong` số tin trở lên yêu cầu.
    """
    if similarity.empty:
        return pd.DataFrame(
            columns=["title_a", "title_b", "cosine",
                     "skill_chung", "chi_title_a", "chi_title_b"]
        )

    ho_so = M.groupby(titles.reindex(M.index).values).mean()

    rows = []
    for _, cap in similarity.head(top).iterrows():
        a = ho_so.loc[cap["title_a"]]
        b = ho_so.loc[cap["title_b"]]

        co_a = a >= nguong
        co_b = b >= nguong

        rows.append({
            "title_a": cap["title_a"],
            "title_b": cap["title_b"],
            "cosine": cap["cosine"],
            "skill_chung": ", ".join(ho_so.columns[co_a & co_b]),
            "chi_title_a": ", ".join(ho_so.columns[co_a & ~co_b]),
            "chi_title_b": ", ".join(ho_so.columns[~co_a & co_b]),
        })

    return pd.DataFrame(rows)


# Chạy toàn bộ RQ3

def run_rq3(M, titles, iterations=config.BOOTSTRAP_ITERATIONS):
    disp, skipped = compute_title_dispersion(M, titles)

    if disp.empty:
        return {
            "status": f"no title reaches {config.MIN_POSTINGS_PER_TITLE} postings",
            "skipped_titles": skipped,
            "dispersion": disp,
        }

    similarity = compute_title_similarity(M, titles)

    return {
        "status": "ok",
        "dispersion": add_baselines(disp, M, iterations),
        "skipped_titles": skipped,
        "title_similarity": similarity,
        "notable": notable_title_pairs(M, titles, similarity),
    }