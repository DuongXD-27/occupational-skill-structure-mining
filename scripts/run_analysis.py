"""Chạy toàn bộ RQ2-RQ4 và ghi mọi kết quả ra reports/analysis/.

    python scripts/run_analysis.py                  # dữ liệu giả
    python scripts/run_analysis.py --real           # dữ liệu thật của Cường

Ghi ra đúng những thứ task mục 6 đòi: bảng CSV cho từng kết quả, và hình PNG
cho PCA.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis import loaders, plots, rq2, rq3, rq4, synthetic

ap = argparse.ArgumentParser()
ap.add_argument("--real", action="store_true",
                help="đọc ma trận thật thay vì sinh dữ liệu giả")
ap.add_argument("--n", type=int, default=400, help="số tin giả cần sinh")
ap.add_argument("--outdir", default="reports/analysis")
args = ap.parse_args()

OUT = Path(args.outdir)
OUT.mkdir(parents=True, exist_ok=True)


def ghi(bang, ten):
    """Ghi một bảng ra CSV, in lại dòng xác nhận.

    Bảng nào chưa có thì báo rồi đi tiếp, không làm hỏng cả lượt chạy.
    """
    if bang is None:
        print(f"  BỎ QUA {ten} — chưa có hàm nào sinh ra bảng này")
        return

    duong_dan = OUT / f"{ten}.csv"
    bang.to_csv(duong_dan, index=False, encoding="utf-8-sig")
    print(f"  {duong_dan}   ({len(bang)} dòng)")


# ------------------------------------------------------------ dữ liệu
if args.real:
    try:
        M = loaders.load_skill_matrix()
    except FileNotFoundError:
        # thiếu file ma trận thì dựng lại từ file dạng dài
        print("  Không thấy job_skill_matrix.parquet, thử job_skills.parquet")
        M = loaders.load_from_job_skills()
    for canh_bao in loaders.warn_about(M):
        print(f"  CẢNH BÁO: {canh_bao}")
    titles = pd.read_parquet("data/processed/jobs.parquet").set_index(
        "job_id")["normalized_job_title"]
    nguon = "dữ liệu thật"
else:
    df = synthetic.generate_jobs(n=args.n)
    M = synthetic.build_matrix(df)
    titles = df.set_index("job_id")["normalized_job_title"]
    nguon = f"DỮ LIỆU GIẢ ({args.n} tin) — số liệu này không được đưa vào báo cáo"

print(f"\nNguồn: {nguon}")
print(f"Ma trận: {M.shape[0]} tin x {M.shape[1]} skill\n")


# ----------------------------------------------------------------- RQ2
print("RQ2 — nhu cầu và cấu trúc kỹ năng")
r2 = rq2.run_rq2(M)

ghi(r2.get("skill_frequency"), "rq2_skill_frequency")
ghi(r2.get("pairs"), "rq2_skill_pairs")
ghi(
    pd.DataFrame(
        sorted(r2["communities"].items(), key=lambda kv: (kv[1], kv[0])),
        columns=["skill", "community"],
    ),
    "rq2_skill_communities",
)
ghi(pd.DataFrame([r2["skills_per_posting"]]), "rq2_skills_per_posting")


# ----------------------------------------------------------------- RQ3
print("\nRQ3 — độ nhất quán giữa title và skill")
r3 = rq3.run_rq3(M, titles)

if r3["status"] != "ok":
    print(f"  BỎ QUA: {r3['status']}")
    ghi(r3.get("skipped_titles"), "rq3_skipped_titles")
else:
    ghi(r3.get("dispersion"), "rq3_title_dispersion")
    ghi(r3.get("title_similarity"), "rq3_title_similarity")
    ghi(r3.get("notable"), "rq3_notable_pairs")
    ghi(r3.get("skipped_titles"), "rq3_skipped_titles")


# ----------------------------------------------------------------- RQ4
print("\nRQ4 — cấu trúc nghề nghiệp hình thành từ dữ liệu")
r4 = rq4.run_rq4(M, titles=titles)

print(f"  {r4['message']}")

if r4["status"] == "skipped":
    print("  Không ghi kết quả RQ4 — chưa đủ dữ liệu.")
else:
    print(f"  Chọn k = {r4['chosen_k']}")

    ghi(r4.get("sweep"), "rq4_k_sweep")
    ghi(r4.get("profiles"), "rq4_cluster_profiles")
    ghi(r4["labels"].reset_index(), "rq4_cluster_assignment")
    ghi(r4.get("pca"), "rq4_pca_coordinates")

    if "unblinded" in r4:
        # bảng task mục 6 đòi: cụm gồm skill gì, rồi mới tới title nào trong đó
        ghi(r4["profiles"].merge(r4["unblinded"], on="cluster"),
            "rq4_clusters_with_titles")
        ghi(pd.DataFrame([r4["agreement"]]), "rq4_agreement")

    print(f"  {plots.ve_pca(r4, titles, OUT / 'rq4_pca.png')}")
    print(f"  {plots.ve_quet_k(r4['sweep'], r4['chosen_k'], OUT / 'rq4_sweep_k.png')}")


print(f"\nXong. Mọi kết quả nằm trong {OUT}/")
if not args.real:
    print("Nhắc lại: đây là dữ liệu giả, dùng để kiểm tra code chạy đúng.")
