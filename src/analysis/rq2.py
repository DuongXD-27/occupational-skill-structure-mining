"""RQ2 — thị trường cần skill nào, và skill nào đi cùng nhau."""

import itertools

import networkx as nx
import numpy as np
import pandas as pd

from . import config


# Bước 1 — Đếm skill

def compute_skill_frequency(M):
    """Đếm số tin chứa mỗi skill."""
    so_tin = len(M)
    so_tin_co_skill = M.sum()

    out = pd.DataFrame({
        "skill": M.columns,
        "n_postings": so_tin_co_skill.values,
    })
    out["share"] = (out["n_postings"] / so_tin).round(4)

    return out.sort_values(
        "n_postings", ascending=False
    ).reset_index(drop=True)


def skills_per_posting(M):
    """Kiểm tra mỗi tin trung bình có bao nhiêu skill."""
    so_skill_moi_tin = M.sum(axis=1)

    return {
        "mean": round(float(so_skill_moi_tin.mean()), 2),
        "median": float(so_skill_moi_tin.median()),
        "p10": float(so_skill_moi_tin.quantile(0.10)),
        "p90": float(so_skill_moi_tin.quantile(0.90)),
        "postings_below_min": int(
            (so_skill_moi_tin < config.MIN_SKILLS_PER_POSTING).sum()
        ),
    }


# Bước 2 — Đếm cặp skill

def compute_cooccurrence(M, min_joint=config.MIN_COOCCURRENCE):
    """Đếm số tin chứa cả hai skill."""
    bang_cap = M.T.values @ M.values
    ten_skill = list(M.columns)

    rows = []

    for i, j in itertools.combinations(range(len(ten_skill)), 2):
        so_tin_co_ca_hai = int(bang_cap[i, j])

        if so_tin_co_ca_hai >= min_joint:
            rows.append({
                "skill_a": ten_skill[i],
                "skill_b": ten_skill[j],
                "joint": so_tin_co_ca_hai,
            })

    # columns= là bắt buộc: không cặp nào đạt ngưỡng thì rows rỗng, thiếu
    # columns thì sort_values("joint") nổ KeyError
    return pd.DataFrame(rows, columns=["skill_a", "skill_b", "joint"]).sort_values(
        "joint", ascending=False
    ).reset_index(drop=True)


# Bước 3–5 — Tính mức độ liên quan

def compute_associations(M, pairs=None):
    """Tính Lift, NPMI và Jaccard cho từng cặp skill."""
    if pairs is None:
        pairs = compute_cooccurrence(M)

    if pairs.empty:
        return pairs.assign(lift=[], npmi=[], jaccard=[])

    so_tin = len(M)
    so_tin_co_skill = M.sum()

    # Số tin có từng skill của cặp
    n_a = pairs["skill_a"].map(so_tin_co_skill)
    n_b = pairs["skill_b"].map(so_tin_co_skill)

    # Xác suất xuất hiện
    p_a = n_a / so_tin
    p_b = n_b / so_tin
    p_thuc_te = pairs["joint"] / so_tin

    # Xác suất nếu hai skill độc lập
    p_ngau_nhien = p_a * p_b

    out = pairs.copy()

    # So sánh thực tế với ngẫu nhiên
    out["lift"] = (
        p_thuc_te / p_ngau_nhien
    ).round(3)

    out["npmi"] = (
        np.log(p_thuc_te / p_ngau_nhien)
        / -np.log(p_thuc_te)
    ).round(3)

    # Jaccard
    so_tin_co_it_nhat_mot = n_a + n_b - pairs["joint"]

    out["jaccard"] = (
        pairs["joint"] / so_tin_co_it_nhat_mot
    ).round(3)

    return out.sort_values(
        "npmi", ascending=False
    ).reset_index(drop=True)


# Bước 6 — Gom skill thành nhóm

def detect_communities(assoc, weight="npmi", min_weight=0.0):
    """Gom các skill có liên hệ dương thành các nhóm."""
    canh = assoc[assoc[weight] > min_weight]

    G = nx.Graph()

    G.add_nodes_from(
        set(assoc["skill_a"]) | set(assoc["skill_b"])
    )

    for _, r in canh.iterrows():
        G.add_edge(
            r["skill_a"],
            r["skill_b"],
            weight=float(r[weight])
        )

    cum = nx.community.greedy_modularity_communities(
        G,
        weight="weight"
    )

    return {
        skill: i
        for i, nhom in enumerate(cum)
        for skill in nhom
    }


# Chạy toàn bộ RQ2

def run_rq2(M):
    """Chạy toàn bộ phân tích RQ2."""
    assoc = compute_associations(M)

    return {
        "skill_frequency": compute_skill_frequency(M),
        "skills_per_posting": skills_per_posting(M),
        "pairs": assoc,
        "communities": (
            detect_communities(assoc)
            if not assoc.empty
            else {}
        ),
    }
