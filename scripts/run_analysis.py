"""Chạy toàn bộ RQ2-RQ4 và ghi mọi kết quả ra reports/analysis/.

    python scripts/run_analysis.py                  # dữ liệu giả
    python scripts/run_analysis.py --real           # dữ liệu thật của Cường

Ghi ra đúng những thứ task mục 6 đòi: bảng CSV cho từng kết quả, và hình PNG
cho PCA. Logic nằm ở src/analysis/report.py (dùng chung với pipeline tích hợp).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis import loaders, report, synthetic  # noqa: E402


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser()
    ap.add_argument("--real", action="store_true",
                    help="đọc ma trận thật thay vì sinh dữ liệu giả")
    ap.add_argument("--n", type=int, default=400, help="số tin giả cần sinh")
    ap.add_argument("--clean", default="data/processed/jobs_clean.parquet",
                    help="bảng sạch của cleaner (lấy normalized_job_title)")
    ap.add_argument("--matrix", default="data/features/job_skill_matrix.parquet")
    ap.add_argument("--skills", default="data/features/job_skills.parquet")
    ap.add_argument("--taxonomy", default="taxonomy/skills_taxonomy.csv")
    ap.add_argument("--outdir", default="reports/analysis")
    ap.add_argument("--ignore-quality", action="store_true",
                    help="vẫn chạy khi kiểm tra chất lượng thất bại (chỉ để gỡ lỗi)")
    args = ap.parse_args(argv)

    if args.real:
        loi = report.run_quality_checks(args.clean, args.skills, args.outdir)
        if loi:
            print("\nKIỂM TRA CHẤT LƯỢNG THẤT BẠI — không phân tích (analysis_spec §9):")
            for dong in loi:
                print(f"  - {dong}")
            if not args.ignore_quality:
                return 1
            print("  --ignore-quality: vẫn chạy, KẾT QUẢ KHÔNG ĐƯỢC ĐƯA VÀO BÁO CÁO")
        try:
            M = loaders.load_skill_matrix(args.matrix, taxonomy_path=args.taxonomy)
        except FileNotFoundError:
            # thiếu file ma trận thì dựng lại từ file dạng dài
            print("  Không thấy job_skill_matrix.parquet, thử job_skills.parquet")
            M = loaders.load_from_job_skills(args.skills)
        for canh_bao in loaders.warn_about(M):
            print(f"  CẢNH BÁO: {canh_bao}")
        titles = report.load_titles(args.clean)
        nguon = "dữ liệu thật"
    else:
        df = synthetic.generate_jobs(n=args.n)
        M = synthetic.build_matrix(df)
        titles = df.set_index("job_id")["normalized_job_title"]
        nguon = f"DỮ LIỆU GIẢ ({args.n} tin) — số liệu này không được đưa vào báo cáo"

    print(f"\nNguồn: {nguon}")
    print(f"Ma trận: {M.shape[0]} tin x {M.shape[1]} skill\n")

    status = report.write_analysis(M, titles, args.outdir)

    print(f"\nXong. Mọi kết quả nằm trong {args.outdir}/")
    for rq, item in status.items():
        print(f"  {rq}: {item['status']}" + (f" — {item['reason']}" if item.get("reason") else ""))
    if not args.real:
        print("Nhắc lại: đây là dữ liệu giả, dùng để kiểm tra code chạy đúng.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
