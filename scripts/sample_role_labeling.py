"""Chọn mẫu tin để gán nhãn vai trò và chia lô (report/main.tex §4.6 và phụ lục D).

Mẫu gồm mọi tin bị loại vì ngoài phạm vi (để đánh giá bộ lọc) cộng tin hợp lệ chọn ngẫu nhiên.
Tin trùng không vào mẫu. Thứ tự và cách chia lô chỉ phụ thuộc job_id qua hàm băm, nên chạy lại ra
đúng như cũ và không ai chọn tay tin nào vào lô nào.

    python scripts/sample_role_labeling.py --clean data/processed/jobs_clean.parquet
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd

SALT = "role-sample-v1:"


def _key(job_id: str, salt: str = SALT) -> str:
    return hashlib.sha256((salt + job_id).encode()).hexdigest()


def sample(clean: pd.DataFrame, n: int = 300, k: int = 60, batches: int = 5) -> pd.DataFrame:
    df = clean[~clean["duplicate_flag"].astype(bool)].copy()
    df = df[df["job_text"].fillna("").str.strip() != ""]
    excluded = df[~df["relevance_flag"].astype(bool)]
    kept = df[df["relevance_flag"].astype(bool)]
    n_kept = n - len(excluded)
    if n_kept < 0 or n_kept > len(kept):
        raise ValueError(f"không chọn được {n} tin: {len(excluded)} bị loại, {len(kept)} hợp lệ")
    kept = kept.assign(_h=kept["job_id"].map(_key)).sort_values("_h").head(n_kept)
    out = pd.concat([excluded.assign(stratum="excluded"), kept.assign(stratum="kept")])
    out = out.assign(_o=out["job_id"].map(lambda j: _key(j, "role-batch-v1:"))).sort_values("_o")
    out["batch"] = ""
    out.iloc[:k, out.columns.get_loc("batch")] = "K"
    rest = len(out) - k
    size = -(-rest // batches)
    for i in range(batches):
        out.iloc[k + i * size: k + (i + 1) * size, out.columns.get_loc("batch")] = f"B{i + 1}"
    return out[["job_id", "batch", "stratum"]].reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--clean", default="data/processed/jobs_clean.parquet")
    ap.add_argument("--out", default="data/labels/role_sample.csv")
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--k", type=int, default=60, help="số tin chồng lấn (lô K) để đo kappa")
    ap.add_argument("--batches", type=int, default=5)
    a = ap.parse_args()
    s = sample(pd.read_parquet(a.clean), a.n, a.k, a.batches)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    s.to_csv(a.out, index=False)
    print(s.groupby(["batch", "stratum"]).size().unstack(fill_value=0))


if __name__ == "__main__":
    main()
