"""Ghi dữ liệu giả ra đĩa để mở ra xem được.

    python scripts/make_synthetic_data.py
    python scripts/make_synthetic_data.py --n 1000 --noise 0.3

Ghi hai file CSV vào data/synthetic/:

    synthetic_jobs.csv          mỗi dòng một tin, skill để dạng danh sách chữ
    synthetic_skill_matrix.csv  bảng 0/1 mà các phân tích thật sự đọc

Phân tích KHÔNG cần hai file này — nó gọi thẳng generate_jobs(). Hai file chỉ
để người xem bằng mắt.

Không có gì ở đây là thật. Số liệu này tuyệt đối không được đưa vào báo cáo.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis import synthetic

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=400, help="number of postings")
ap.add_argument("--noise", type=float, default=0.15,
                help="xác suất thêm một skill lạc từ nghề khác")
ap.add_argument("--drop", type=float, default=0.20,
                help="xác suất bỏ bớt một skill lõi")
ap.add_argument("--outdir", default="data/synthetic")
args = ap.parse_args()

out = Path(args.outdir)
out.mkdir(parents=True, exist_ok=True)

df = synthetic.generate_jobs(n=args.n, noise=args.noise, drop=args.drop)
M = synthetic.build_matrix(df)

jobs = df.copy()
jobs["extracted_skills"] = jobs["extracted_skills"].apply(", ".join)
jobs["skill_count"] = df["extracted_skills"].apply(len)
jobs.to_csv(out / "synthetic_jobs.csv", index=False, encoding="utf-8-sig")
M.to_csv(out / "synthetic_skill_matrix.csv", encoding="utf-8-sig")

print(f"Wrote {out / 'synthetic_jobs.csv'}         {len(jobs)} rows")
print(f"Wrote {out / 'synthetic_skill_matrix.csv'}  "
      f"{M.shape[0]} rows x {M.shape[1]} skills")
print()
print("First 5 postings:")
print(jobs.head(5).to_string(index=False))
print()
print("Postings per planted family:")
print(df["true_family"].value_counts().to_string())
print()
print("NOTE: synthetic data, for testing the code only. Never report these numbers.")
