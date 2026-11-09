"""Dựng tools/gold_review/index.html từ gold nháp, góp ý lượt hai và taxonomy.

    python tools/gold_review/build.py

Trang chạy hoàn toàn trên máy (mở index.html bằng trình duyệt), lưu tạm trong
trình duyệt và xuất kết quả ra data/evaluation/reviews/gold_review_<tên>.json.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.parser.evaluation import gold_split  # noqa: E402

HERE = Path(__file__).resolve().parent
GOLD = ROOT / "data/evaluation/gold_jobs.draft.jsonl"
PASS2 = ROOT / "data/evaluation/review_pass2.jsonl"
TAXONOMY = ROOT / "taxonomy/skills_taxonomy.csv"
KAPPA_SIZE = 18   # quyết định F.3: 15–20 tin gán độc lập

# Quy ước chung chốt sau lượt rà soát hai: góp ý "thiếu" của các kỹ năng này được thêm luôn,
# người duyệt không phải chọn. Xem report/main.tex phụ lục C.9.
AUTO_ADD = {
    "API Design": "Quy ước 05/11 (Cường): tin nhắc tới xây dựng, tích hợp hoặc làm việc với API "
                  "(REST, RESTful, SOAP, GraphQL…) thì gán API Design.",
}


def kappa_ids(job_ids):
    """18 tin cố định: thứ tự theo sha256('kappa-v1:' + job_id) (report/main.tex §4.4)."""
    return set(sorted(job_ids, key=lambda j: hashlib.sha256(f"kappa-v1:{j}".encode()).hexdigest())[:KAPPA_SIZE])


def _list(v):
    return v if isinstance(v, list) else (ast.literal_eval(v) if v else [])


def build_data():
    gold = [json.loads(l) for l in GOLD.open(encoding="utf-8") if l.strip()]
    pass2 = [json.loads(l) for l in PASS2.open(encoding="utf-8") if l.strip()]
    kp = kappa_ids([g["job_id"] for g in gold])
    jobs = []
    for g in gold:
        labels = [{"n": a["canonical_name"], "id": a["skill_id"], "s": a["start"], "e": a["end"]} for a in _list(g["annotations"])]
        sugs = []
        for x in pass2:
            if x["job_id"] != g["job_id"]:
                continue
            d = {"k": x["kind"], "a": x["action"], "lv": x["level"], "n": x["canonical_name"], "id": x["skill_id"], "why": x["reason"]}
            for src, dst in (("suggested_start", "s"), ("suggested_end", "e"), ("suggested_canonical_name", "rn"), ("suggested_skill_id", "rid")):
                if src in x:
                    d[dst] = x[src]
            if x["kind"] == "missing" and x["canonical_name"] in AUTO_ADD:
                d["auto"], d["autoWhy"] = "add", AUTO_ADD[x["canonical_name"]]
            if x["kind"] == "label":
                d["li"] = next(i for i, l in enumerate(labels) if l["id"] == x["skill_id"])
            sugs.append(d)
        jobs.append({"id": g["job_id"], "src": g["source"], "t": g["raw_job_title"], "url": g["source_url"], "x": g["text"],
                     "sp": gold_split(g["job_id"]), "kp": g["job_id"] in kp, "note": g.get("review_notes") or "", "L": labels, "S": sugs})
    tax = []
    for row in csv.DictReader(TAXONOMY.open(encoding="utf-8-sig")):
        aliases = [a.strip() for a in (row["aliases"] or "").split(";") if a.strip()]
        if row["abbreviation"]:
            aliases.append(row["abbreviation"])
        tax.append([row["skill_id"], row["canonical_name"], aliases])
    return {"jobs": jobs, "tax": tax}


def main():
    data = json.dumps(build_data(), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = (HERE / "template.html").read_text(encoding="utf-8")
    page = page.replace("<!--DATA-->", f'<script type="application/json" id="gold-data">{data}</script>')
    page = page.replace("<!--APP-->", "<script>\n" + (HERE / "app.js").read_text(encoding="utf-8") + "</script>")
    (HERE / "index.html").write_text(page, encoding="utf-8")
    print(f"Đã ghi {HERE / 'index.html'}")


if __name__ == "__main__":
    main()
