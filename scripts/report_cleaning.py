"""
Tạo lại bảng sạch, báo cáo chất lượng và báo cáo RQ1 từ CÙNG một lần chạy cleaner,
để các con số trong hai báo cáo luôn khớp nhau.

    python scripts/report_cleaning.py --raw data/pilot/jobs_pilot.jsonl
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.cleaner.pipeline import run_pipeline  # noqa: E402
from src.cleaner.rq1 import compute_rq1, write_rq1  # noqa: E402


def _pct(a, b):
    return f"{a} ({a / b * 100:.1f}%)" if b else str(a)


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--clean", default="data/processed/jobs_clean.parquet")
    ap.add_argument("--rq1-dir", default="reports/analysis/rq1")
    ap.add_argument("--report-dir", default="reports/data_quality")
    args = ap.parse_args(argv)

    stats = run_pipeline(args.raw, args.clean)
    df = pd.read_parquet(args.clean)
    flags = [json.loads(l)["quality_flags"] for l in Path(stats["quality_log"]).read_text(encoding="utf-8").splitlines()]
    flag_counts = collections.Counter(f for fl in flags for f in fl)
    raw_version = sorted(df["parser_version"].dropna().unique())
    n = len(df)
    rel, dup = df["relevance_flag"], df["duplicate_flag"]
    excl = df.loc[~rel, "exclusion_reason"].value_counts()

    out = Path(args.report_dir)
    out.mkdir(parents=True, exist_ok=True)
    q = [
        "# Báo cáo chất lượng dữ liệu — Tập pilot",
        "",
        f"> Nguồn: `{Path(args.raw).as_posix()}` (parser {', '.join(raw_version)}, nguồn: ITviec).",
        "> Sinh tự động bởi `scripts/report_cleaning.py`; cùng lần chạy với `rq1_results.md`.",
        "",
        "## 1. Tóm tắt pipeline",
        "",
        "| Chỉ số | Số lượng |",
        "|---|---|",
        f"| Tổng bản ghi đầu vào | {stats['n_input']} |",
        f"| Bản ghi trong bảng sạch (không xóa bản ghi nào) | {n} |",
        f"| Lỗi kỹ thuật QR-01 (`exclusion_reason=SCRAPE_ERROR`) | {stats['n_scrape_error']} |",
        f"| Ngoài phạm vi (`relevance_flag=false`) | {_pct(int((~rel).sum()), n)} |",
        f"| Trùng lặp (`duplicate_flag=true`) | {_pct(int(dup.sum()), n)} |",
        f"| Vừa ngoài phạm vi vừa trùng lặp (tính một lần) | {int((~rel & dup).sum())} |",
        f"| **Tin hợp lệ (`relevance=true AND duplicate=false`)** | **{int((rel & ~dup).sum())}** |",
        "",
        "Lý do loại trừ:",
        "",
        "| `exclusion_reason` | Số lượng |",
        "|---|---|",
        *[f"| `{k}` | {v} |" for k, v in excl.items()],
        "",
        "## 2. Kết quả chuẩn hóa",
        "",
        "| Trường | Có giá trị | Thiếu |",
        "|---|---|---|",
        f"| `normalized_job_title` | {int(df['normalized_job_title'].notna().sum())} | {int(df['normalized_job_title'].isna().sum())} |",
        f"| `normalized_location` | {int(df['normalized_location'].notna().sum())} | {int(df['normalized_location'].isna().sum())} |",
        f"| `job_text` | {int(df['job_text'].notna().sum())} | {int(df['job_text'].isna().sum())} |",
        "",
        f"- Số chức danh thô khác biệt (trim + lowercase, toàn bảng): {stats['unique_raw_titles']}",
        f"- Số chức danh chuẩn hóa khác biệt (toàn bảng): {stats['unique_normalized_titles']}",
        f"- Số địa điểm chuẩn hóa khác biệt: {stats['unique_normalized_locations']}",
        "",
        "## 3. Cờ chất lượng",
        "",
        "Cờ không thuộc schema 22 trường nên được ghi ở file riêng "
        f"`{Path(stats['quality_log']).as_posix()}`.",
        "",
        "| Cờ | Số lượng |",
        "|---|---|",
        *[f"| `{k}` | {v} |" for k, v in flag_counts.most_common()],
        "",
        "## 4. Ghi chú",
        "",
        "> **QR-03 (Kinh nghiệm):** Theo quyết định 2026-10-04, chỉ giữ `raw_experience` nguyên văn;",
        "> cleaner không parse số năm. Bản ghi thiếu dữ liệu nguồn mang cờ `MISSING_EXPERIENCE`;",
        "> giá trị hình thức làm việc bị crawler gán nhầm mang thêm `SCRAPER_FIELD_MISMATCH`.",
        "",
        "> **QR-04 (Chức danh):** Bỏ cấp bậc thuần túy (Senior/Junior/Middle/Fresher) và hậu tố",
        "> công nghệ rõ ràng (mọi mục đều là công cụ trong taxonomy) theo quyết định 2026-10-03 §C.",
        "> Phần trong ngoặc mô tả chuyên môn/lĩnh vực được giữ. Cờ `SENIORITY_REMOVED`,",
        "> `TECH_SUFFIX_REMOVED` ghi lại phần đã bỏ để kiểm toán.",
        "",
        "> **QR-05 (Trùng lặp):** Trùng chính xác khi cùng `source_url`. Trùng gần khi đồng thời khớp",
        "> `company`, độ tương đồng Jaccard của `normalized_job_title` ≥ 0.60, khớp",
        "> `normalized_location`, và TF-IDF cosine trên `job_description` ≥ 0.80. Luồng JD-only",
        "> (cosine ≥ 0.95) vẫn là đề xuất chờ Leader duyệt nên tắt mặc định.",
        "",
    ]
    (out / "quality_report.md").write_text("\n".join(q), encoding="utf-8")

    write_rq1(args.clean, args.rq1_dir)
    res = compute_rq1(df)
    m = dict(zip(res["summary"]["metric"], res["summary"]["value"]))
    r = [
        "# Kết quả RQ1 — Chức danh công việc",
        "",
        "> **RQ1:** Những chức danh nào tồn tại và mỗi chức danh phổ biến ra sao?",
        "> Sinh tự động bởi `scripts/report_cleaning.py` (module `src/cleaner/rq1.py`);",
        f"> bảng và biểu đồ đầy đủ ở `{Path(args.rq1_dir).as_posix()}/`.",
        "",
        f"**Tập phân tích:** {m['n_postings']} tin (`relevance_flag=true` VÀ `duplicate_flag=false`), "
        "cùng con số với báo cáo chất lượng.",
        "",
    ]
    if m["sample_note"] == "pipeline_test":
        r += [
            "> ⚠️ Dưới 1.000 tin: đây là kiểm thử pipeline trên tập pilot, chưa phải phát hiện nghiên cứu",
            "> (analysis_spec §8).",
            "",
        ]
    r += [
        "## Bảng tổng hợp",
        "",
        "| Chỉ số | Giá trị | Ý nghĩa |",
        "|---|---|---|",
        *[f"| `{a}` | {b} | {c} |" for a, b, c in res["summary"].itertuples(index=False)],
        "",
        "## Top 20 chức danh chuẩn hóa",
        "",
        "| Hạng | Chức danh chuẩn hóa | Số tin | Tỷ trọng |",
        "|---|---|---|---|",
        *[f"| {a} | {b} | {c} | {d:.1%} |" for a, b, c, d in res["top"].itertuples(index=False)],
        "",
        f"Danh sách {len(res['rare'])} chức danh hiếm (≤ 2 tin) kèm công ty và URL: "
        f"`{Path(args.rq1_dir).as_posix()}/rq1_rare_titles.csv`.",
        "",
    ]
    (out / "rq1_results.md").write_text("\n".join(r), encoding="utf-8")
    print(json.dumps({k: v for k, v in stats.items() if k != "scrape_error_job_ids"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
