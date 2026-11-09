"""
src/cleaner/rq1.py
RQ1 — Những chức danh nào tồn tại và mức độ phổ biến (report/main.tex §4.5).

Chỉ dùng tin relevance_flag=true AND duplicate_flag=false.

Chỉ số:
- Số tin giữ lại sau làm sạch (mẫu số cho mọi tỷ lệ).
- Số chức danh thô khác biệt (thô = trim + lowercase; khoảng trắng liên tiếp gộp làm
  một vì crawler lưu nguyên văn bản HTML) / số chức danh chuẩn hóa khác biệt.
- Tỷ lệ nén = số chức danh chuẩn hóa ÷ số chức danh thô.
- Độ tập trung: tỷ trọng top-1/5/10 và chỉ số HHI.
- Entropy Shannon (bit) và entropy chuẩn hóa (÷ log2 số chức danh).
- Tỷ lệ chức danh hiếm (≤ 2 tin) và các công ty đứng sau chúng.

Đầu ra: 3 bảng (tổng hợp, top 20, chức danh hiếm kèm công ty và URL) và 2 biểu đồ
(cột top 20, hạng–tần suất log-log).

Chạy:
    python -m src.cleaner.rq1 --clean data/processed/jobs_clean.parquet --out reports/analysis/rq1
Trong pipeline: entry point ``src.cleaner.rq1:run``.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

RARE_MAX_POSTINGS = 2
TOP_N = 20
RESEARCH_MIN_POSTINGS = 1000  # quy mô mục tiêu của project_scope §9

ARTIFACTS = (
    "rq1_summary.csv",
    "rq1_top20_titles.csv",
    "rq1_rare_titles.csv",
    "rq1_top20_titles.png",
    "rq1_rank_frequency.png",
)


def raw_title_key(title: Optional[str]) -> Optional[str]:
    """Khóa đếm chức danh thô: trim + lowercase (gộp khoảng trắng)."""
    if title is None:
        return None
    key = " ".join(str(title).split()).lower()
    return key or None


def read_clean(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".jsonl":
        rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        return pd.DataFrame(rows, dtype=object)
    return pd.read_parquet(path)


def eligible(df: pd.DataFrame) -> pd.DataFrame:
    mask = (df["relevance_flag"] == True) & (df["duplicate_flag"] == False)  # noqa: E712
    return df.loc[mask].copy()


def _entropy(counts: pd.Series) -> float:
    total = counts.sum()
    return float(-sum((c / total) * math.log2(c / total) for c in counts if c > 0))


def compute_rq1(clean: pd.DataFrame) -> dict:
    """Tính các bảng RQ1 từ bảng sạch (đủ 22 trường)."""
    df = eligible(clean)
    n = len(df)
    if n == 0:
        raise ValueError("RQ1: không có tin hợp lệ (relevance=true, duplicate=false)")
    if df["normalized_job_title"].isna().any():
        raise ValueError("RQ1: có tin hợp lệ thiếu normalized_job_title")

    raw_keys = df["raw_job_title"].map(raw_title_key)
    norm_counts = df["normalized_job_title"].value_counts()
    raw_counts = raw_keys.value_counts()

    n_raw, n_norm = int(raw_counts.size), int(norm_counts.size)
    shares = norm_counts / n
    rare = norm_counts[norm_counts <= RARE_MAX_POSTINGS]
    rare_jobs = df[df["normalized_job_title"].isin(rare.index)]
    rare_companies = rare_jobs["company"].fillna("(không rõ)").map(lambda c: " ".join(str(c).split()))

    summary = [
        ("n_postings", n, "Số tin hợp lệ (relevance=true, duplicate=false)"),
        ("n_raw_titles", n_raw, "Số chức danh thô khác biệt (trim + lowercase)"),
        ("n_normalized_titles", n_norm, "Số chức danh chuẩn hóa khác biệt"),
        ("compression_ratio", round(n_norm / n_raw, 4), "Số chức danh chuẩn hóa ÷ số chức danh thô"),
        ("top1_share", round(float(shares.iloc[:1].sum()), 4), "Tỷ trọng tin của chức danh phổ biến nhất"),
        ("top5_share", round(float(shares.iloc[:5].sum()), 4), "Tỷ trọng tin của 5 chức danh phổ biến nhất"),
        ("top10_share", round(float(shares.iloc[:10].sum()), 4), "Tỷ trọng tin của 10 chức danh phổ biến nhất"),
        ("hhi", round(float((shares ** 2).sum()), 4), "Herfindahl–Hirschman trên tỷ trọng chức danh chuẩn hóa"),
        ("entropy_raw_bits", round(_entropy(raw_counts), 4), "Entropy Shannon của chức danh thô"),
        ("entropy_normalized_bits", round(_entropy(norm_counts), 4), "Entropy Shannon của chức danh chuẩn hóa"),
        ("entropy_normalized_ratio",
         round(_entropy(norm_counts) / math.log2(n_norm), 4) if n_norm > 1 else 0.0,
         "Entropy chuẩn hóa ÷ log2(số chức danh); 1 = phân bổ đều"),
        ("n_rare_titles", int(rare.size), f"Số chức danh chuẩn hóa có ≤ {RARE_MAX_POSTINGS} tin"),
        ("rare_title_share", round(rare.size / n_norm, 4), "Tỷ lệ chức danh hiếm trên tổng số chức danh chuẩn hóa"),
        ("rare_posting_share", round(len(rare_jobs) / n, 4), "Tỷ lệ tin thuộc chức danh hiếm"),
        ("n_companies_behind_rare", int(rare_companies.nunique()), "Số công ty đăng các chức danh hiếm"),
        ("top3_company_share_of_rare",
         round(float(rare_companies.value_counts().iloc[:3].sum() / len(rare_jobs)), 4) if len(rare_jobs) else 0.0,
         "Tỷ trọng tin hiếm đến từ 3 công ty đăng nhiều nhất"),
        ("sample_note",
         "pipeline_test" if n < RESEARCH_MIN_POSTINGS else "research",
         f"Dưới {RESEARCH_MIN_POSTINGS} tin: chỉ là kiểm thử pipeline, không phải phát hiện nghiên cứu"),
    ]
    summary_df = pd.DataFrame(summary, columns=["metric", "value", "description"])

    top = norm_counts.head(TOP_N).rename_axis("normalized_job_title").reset_index(name="n_postings")
    top.insert(0, "rank", range(1, len(top) + 1))
    top["share"] = (top["n_postings"] / n).round(4)

    rare_rows = []
    for title, group in rare_jobs.groupby("normalized_job_title", sort=True):
        companies = sorted({" ".join(str(c).split()) for c in group["company"].dropna()})
        rare_rows.append({
            "normalized_job_title": title,
            "n_postings": len(group),
            "companies": "; ".join(companies),
            "source_urls": "; ".join(group["source_url"].astype(str)),
        })
    rare_df = pd.DataFrame(rare_rows, columns=["normalized_job_title", "n_postings", "companies", "source_urls"])

    return {"summary": summary_df, "top": top, "rare": rare_df, "counts": norm_counts}


def _plots(result: dict, out_dir: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    top = result["top"]
    fig, ax = plt.subplots(figsize=(9, max(3, 0.32 * len(top) + 1)))
    ax.barh(top["normalized_job_title"][::-1], top["n_postings"][::-1], color="#3b6ea5")
    ax.set_xlabel("Số tin")
    ax.set_title(f"RQ1 — Top {len(top)} chức danh chuẩn hóa")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_dir / "rq1_top20_titles.png", dpi=150)
    plt.close(fig)

    counts = result["counts"].values
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.loglog(range(1, len(counts) + 1), counts, marker="o", linestyle="none", markersize=3, color="#3b6ea5")
    ax.set_xlabel("Hạng chức danh (log)")
    ax.set_ylabel("Số tin (log)")
    ax.set_title("RQ1 — Phân bố hạng–tần suất")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_dir / "rq1_rank_frequency.png", dpi=150)
    plt.close(fig)


def write_rq1(clean_path: str | Path, out_dir: str | Path) -> dict:
    """Tính RQ1 và ghi 3 bảng + 2 biểu đồ vào out_dir. Trả object trạng thái RQ1."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = compute_rq1(read_clean(clean_path))
    result["summary"].to_csv(out_dir / "rq1_summary.csv", index=False, encoding="utf-8")
    result["top"].to_csv(out_dir / "rq1_top20_titles.csv", index=False, encoding="utf-8")
    result["rare"].to_csv(out_dir / "rq1_rare_titles.csv", index=False, encoding="utf-8")
    _plots(result, out_dir)
    return {"RQ1": {"status": "completed", "artifacts": list(ARTIFACTS)}}


def run(context):
    """Entry point cho src.pipeline: đọc paths['clean'], ghi vào thư mục paths['rq1']."""
    return write_rq1(context.paths["clean"], context.paths["rq1"])


def main(argv: Optional[list[str]] = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Tính RQ1 từ bảng sạch.")
    parser.add_argument("--clean", default="data/processed/jobs_clean.parquet")
    parser.add_argument("--out", default="reports/analysis/rq1")
    args = parser.parse_args(argv)
    status = write_rq1(args.clean, args.out)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
