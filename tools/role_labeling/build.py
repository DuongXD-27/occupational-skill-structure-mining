"""Dựng tools/role_labeling/index.html để gán nhãn vai trò trên máy, không cần mạng.

    python tools/role_labeling/build.py --clean data/processed/jobs_clean.parquet

Trang nhúng văn bản các tin trong data/labels/role_sample.csv, nên index.html KHÔNG được commit
(.gitignore đã chặn). Chia sẻ file này cho thành viên qua thư mục chung của nhóm.
Hướng dẫn: report/main.tex phụ lục D
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

ROLES = [
    ("DA", "Phân tích dữ liệu & BI", "Báo cáo, dashboard, phân tích trả lời câu hỏi kinh doanh"),
    ("DE", "Kỹ nghệ & quản trị dữ liệu", "Pipeline, kho/hồ dữ liệu, governance, chất lượng dữ liệu"),
    ("DS", "Khoa học dữ liệu", "Mô hình thống kê/dự đoán để ra quyết định, thí nghiệm A/B"),
    ("MLE", "Kỹ sư học máy (gồm MLOps)", "Huấn luyện, tối ưu, triển khai mô hình ML/DL"),
    ("AIE", "Kỹ sư ứng dụng AI (LLM)", "Sản phẩm dùng mô hình có sẵn: LLM API, RAG, agent, prompt"),
    ("BA", "Phân tích nghiệp vụ", "Tài liệu yêu cầu, user story, quy trình; không phải phân tích số liệu"),
    ("OTHER", "Không phải Data/AI", "Phần mềm, hạ tầng, DBA, quản lý, kinh doanh; Data/AI < 1/3 công việc"),
]


def build_data(clean: pd.DataFrame, sample: pd.DataFrame) -> dict:
    by_id = clean.set_index("job_id")
    jobs = []
    for r in sample.itertuples():
        row = by_id.loc[r.job_id]
        jobs.append({
            "id": r.job_id,
            "b": r.batch,
            "d": (row.get("job_description") or "").strip(),
            "q": (row.get("job_requirements") or "").strip(),
        })
    return {"version": "role-labels-v1", "roles": ROLES, "jobs": jobs}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--clean", default=str(ROOT / "data/processed/jobs_clean.parquet"))
    ap.add_argument("--sample", default=str(ROOT / "data/labels/role_sample.csv"))
    ap.add_argument("--out", default=str(HERE / "index.html"))
    a = ap.parse_args()
    data = build_data(pd.read_parquet(a.clean), pd.read_csv(a.sample))
    html = (HERE / "template.html").read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = html.replace("/*__DATA__*/", payload).replace("/*__APP__*/", (HERE / "app.js").read_text(encoding="utf-8"))
    Path(a.out).write_text(html, encoding="utf-8")
    print(f"{a.out}: {len(data['jobs'])} tin")


if __name__ == "__main__":
    main()
