"""Gộp các file gán nhãn vai trò, tính kappa cho tin được gán bởi nhiều người, liệt kê bất đồng.

    python scripts/merge_role_labels.py
    python scripts/merge_role_labels.py --reviews "data/labels/role_reviews/*.json"

Đầu vào: các file `role_labels_<tên>.json` xuất từ tools/role_labeling (định dạng role-labels-v1).
Kết quả thống nhất sau họp (nếu có): data/labels/role_adjudicated.csv với cột
job_id, primary, secondary, reason; dòng ở đây ghi đè bất đồng.

Đầu ra (cùng thư mục với --out):
  role_labels.csv     nhãn cuối, một dòng mỗi tin; tin còn bất đồng có status=conflict, primary rỗng
  role_conflicts.csv  các tin mà người gán chọn vai trò chính khác nhau
  role_summary.json   số nhãn theo vai trò, kappa từng cặp người gán, các cặp vai trò hay bị nhầm
Hướng dẫn: report/main.tex phụ lục D
"""
from __future__ import annotations

import argparse
import glob
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROLES = ["DA", "DE", "DS", "MLE", "AIE", "BA", "OTHER"]
FORMAT = "role-labels-v1"


def load_reviews(pattern: str) -> dict[str, list[dict]]:
    """{người gán: [nhãn]}. Bỏ qua file sai định dạng hoặc nhãn ngoài 7 vai trò."""
    out: dict[str, list[dict]] = {}
    for f in sorted(glob.glob(pattern)):
        doc = json.loads(Path(f).read_text(encoding="utf-8"))
        if doc.get("format") != FORMAT:
            raise ValueError(f"{f}: định dạng {doc.get('format')!r}, cần {FORMAT!r}")
        name = (doc.get("labeler") or Path(f).stem).strip()
        bad = [l["job_id"] for l in doc["labels"] if l["primary"] not in ROLES or (l.get("secondary") or "") not in ROLES + [""]]
        if bad:
            raise ValueError(f"{f}: nhãn không hợp lệ ở {bad[:5]}")
        out.setdefault(name, []).extend(doc["labels"])
    return out


def cohen_kappa(a: list[str], b: list[str]) -> float | None:
    """Kappa cho hai người trên cùng danh sách tin (nhiều lớp)."""
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def merge(reviews: dict[str, list[dict]], adjudicated: pd.DataFrame | None = None):
    by_job: dict[str, dict[str, dict]] = defaultdict(dict)
    for name, labels in reviews.items():
        for l in labels:
            by_job[l["job_id"]][name] = l          # file sau ghi đè nhãn trước của cùng người
    adj = {} if adjudicated is None else {r.job_id: r for r in adjudicated.itertuples()}

    rows, conflicts = [], []
    for jid, per in sorted(by_job.items()):
        prim = {n: l["primary"] for n, l in per.items()}
        batch = next(iter(per.values())).get("batch", "")
        if jid in adj:
            r = adj[jid]
            rows.append({"job_id": jid, "batch": batch, "primary": r.primary, "secondary": r.secondary if isinstance(r.secondary, str) else "",
                         "status": "adjudicated", "n_labelers": len(per), "unsure": any(l.get("unsure") for l in per.values()),
                         "labelers": ";".join(sorted(per))})
            continue
        agreed = len(set(prim.values())) == 1
        secs = {l.get("secondary", "") for l in per.values()}
        rows.append({"job_id": jid, "batch": batch, "primary": next(iter(prim.values())) if agreed else "",
                     "secondary": secs.pop() if agreed and len(secs) == 1 else "",
                     "status": ("single" if len(per) == 1 else "agreed") if agreed else "conflict",
                     "n_labelers": len(per), "unsure": any(l.get("unsure") for l in per.values()),
                     "labelers": ";".join(sorted(per))})
        if not agreed:
            conflicts.append({"job_id": jid, "batch": batch,
                              **{f"{n}": f"{l['primary']}" + (f"+{l['secondary']}" if l.get("secondary") else "")
                                 + (" (?)" if l.get("unsure") else "") for n, l in sorted(per.items())},
                              "notes": " | ".join(f"{n}: {l['note']}" for n, l in sorted(per.items()) if l.get("note"))})

    pairs = []
    confused = Counter()
    for x, y in itertools.combinations(sorted(reviews), 2):
        shared = [j for j, per in by_job.items() if x in per and y in per]
        a = [by_job[j][x]["primary"] for j in shared]
        b = [by_job[j][y]["primary"] for j in shared]
        k = cohen_kappa(a, b)
        pairs.append({"labelers": [x, y], "shared": len(shared),
                      "agreement": round(sum(p == q for p, q in zip(a, b)) / len(shared), 3) if shared else None,
                      "kappa": None if k is None else round(k, 3)})
        confused.update(tuple(sorted((p, q))) for p, q in zip(a, b) if p != q)

    labels = pd.DataFrame(rows)
    final = labels[labels["primary"] != ""] if len(labels) else labels
    summary = {
        "labelers": {n: len(v) for n, v in reviews.items()},
        "jobs_labeled": len(labels),
        "status": labels["status"].value_counts().to_dict() if len(labels) else {},
        "primary_counts": final["primary"].value_counts().reindex(ROLES, fill_value=0).to_dict() if len(final) else {},
        "pairwise_kappa": pairs,
        "most_confused": [{"roles": list(k), "n": v} for k, v in confused.most_common(10)],
    }
    return labels, pd.DataFrame(conflicts), summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--reviews", default="data/labels/role_reviews/*.json")
    ap.add_argument("--adjudicated", default="data/labels/role_adjudicated.csv")
    ap.add_argument("--out", default="data/labels")
    a = ap.parse_args()
    reviews = load_reviews(a.reviews)
    if not reviews:
        raise SystemExit(f"không có file nào khớp {a.reviews}")
    adj = pd.read_csv(a.adjudicated, dtype=str) if Path(a.adjudicated).exists() else None
    labels, conflicts, summary = merge(reviews, adj)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    labels.to_csv(out / "role_labels.csv", index=False)
    conflicts.to_csv(out / "role_conflicts.csv", index=False)
    (out / "role_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("labelers", "status", "pairwise_kappa")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
