"""Gộp kết quả duyệt gold (data/evaluation/reviews/*.json) thành gold chính thức và tính kappa.

    python scripts/merge_gold_reviews.py                 # gộp mọi file trong reviews/
    python scripts/merge_gold_reviews.py --prefer cuong  # tin hai người duyệt khác nhau: lấy theo Cường

Mỗi file do trang tools/gold_review/index.html xuất ra ("Xuất file kết quả").
Đầu ra:
- data/evaluation/gold_jobs.reviewed.jsonl: các tin đã có người đánh dấu duyệt xong, đúng định
  dạng mà `python -m src.parser evaluate --gold ...` đọc (annotation_status=human_reviewed);
- data/evaluation/review_conflicts.csv: nhãn hai người quyết định khác nhau trên cùng một tin;
- data/evaluation/review_summary.json: số tin đã duyệt, kappa và đồng thuận dương trên nhóm kappa.
"""
from __future__ import annotations

import argparse
import ast
import csv
import glob
import json
import sys
import unicodedata
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.gold_review.build import build_data  # noqa: E402

EVAL = ROOT / "data/evaluation"


def slug(name):
    s = unicodedata.normalize("NFD", name or "").replace("đ", "d").replace("Đ", "D")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return "-".join("".join(c if c.isalnum() else " " for c in s).split())


def final_annotations(job, doc):
    """Cùng quy tắc với finalAnnotations() trong tools/gold_review/app.js."""
    res, rej = doc.get("res", {}), doc.get("rej", {})
    out = []
    for li, lab in enumerate(job["L"]):
        si = next((i for i, s in enumerate(job["S"]) if s["k"] == "label" and s.get("li") == li), None)
        if si is not None:
            sg, ch = job["S"][si], res.get(str(si))
            if ch in (None, "reject"):
                continue
            if ch == "keep":
                out.append(dict(lab))
            elif ch == "fix":
                out.append({**lab, "s": sg["s"], "e": sg["e"]})
            elif ch == "replace":
                out.append({"n": sg["rn"], "id": sg["rid"], "s": sg["s"], "e": sg["e"]})
        elif not rej.get(str(li)):
            out.append(dict(lab))
    for si, sg in enumerate(job["S"]):
        if sg["k"] == "missing" and res.get(str(si)) == "add":
            out.append({"n": sg["n"], "id": sg["id"], "s": sg["s"], "e": sg["e"]})
    out += [dict(a) for a in doc.get("added", [])]
    first = {}
    for a in out:                     # gold: mỗi kỹ năng một bằng chứng (giữ bằng chứng đầu tiên)
        first.setdefault(a["id"], a)
    return list(first.values())


def kappa(sets_a, sets_b, universe):
    """Cohen's kappa trên mọi cặp (tin, kỹ năng) và đồng thuận dương."""
    a = b = c = 0
    for A, B in zip(sets_a, sets_b):
        a += len(A & B); b += len(A - B); c += len(B - A)
    n = universe * len(sets_a)
    d = n - a - b - c
    if n == 0:
        return None, None
    po = (a + d) / n
    pe = ((a + b) / n) * ((a + c) / n) + ((c + d) / n) * ((b + d) / n)
    k = (po - pe) / (1 - pe) if pe < 1 else 1.0
    pos = 2 * a / (2 * a + b + c) if (2 * a + b + c) else 1.0
    return round(k, 4), round(pos, 4)


def load_reviews(paths):
    reviews = {}
    for p in paths:
        d = json.loads(Path(p).read_text(encoding="utf-8"))
        if d.get("format") != "gold-review-v1":
            raise ValueError(f"{p}: không phải file xuất từ trang duyệt gold")
        name = d.get("reviewer") or Path(p).stem
        if slug(name) in {slug(n) for n in reviews}:
            raise ValueError(f"Hai file cùng người duyệt: {name}")
        reviews[name] = d["jobs"]
    return reviews


def merge(reviews, prefer=None, draft_path=EVAL / "gold_jobs.draft.jsonl"):
    data = build_data()
    jobs = {j["id"]: j for j in data["jobs"]}
    universe = len(data["tax"])
    draft = {r["job_id"]: r for r in (json.loads(l) for l in Path(draft_path).open(encoding="utf-8") if l.strip())}
    by_slug = {slug(n): n for n in reviews}
    if prefer and slug(prefer) not in by_slug:
        raise ValueError(f"--prefer {prefer}: không có file duyệt của người này")

    # kappa trên nhóm gán độc lập
    pairs = []
    for x, y in combinations(sorted(reviews), 2):
        ids = [j for j, job in jobs.items() if job["kp"] and reviews[x].get(j, {}).get("indDone") and reviews[y].get(j, {}).get("indDone")]
        A = [{a["id"] for a in reviews[x][j].get("ind", [])} for j in ids]
        B = [{a["id"] for a in reviews[y][j].get("ind", [])} for j in ids]
        k, pos = kappa(A, B, universe)
        pairs.append({"reviewers": [x, y], "jobs": len(ids), "cohen_kappa": k, "positive_agreement": pos})

    rows, conflicts = [], []
    for jid, job in jobs.items():
        done = {n: final_annotations(job, rv[jid]) for n, rv in reviews.items() if rv.get(jid, {}).get("done")}
        if not done:
            continue
        sets = {n: {a["id"]: a for a in anns} for n, anns in done.items()}
        agreed = set.intersection(*(set(s) for s in sets.values()))
        union = set().union(*(set(s) for s in sets.values()))
        for sid in sorted(union - agreed):
            conflicts.append({"job_id": jid, "skill_id": sid,
                              "canonical_name": next(s[sid]["n"] for s in sets.values() if sid in s),
                              **{f"kept_by_{slug(n)}": sid in s for n, s in sets.items()}})
        if prefer and by_slug[slug(prefer)] in sets:
            chosen = sets[by_slug[slug(prefer)]]
            keep = {sid: chosen[sid] for sid in chosen}
        else:                         # không chỉ định: giữ hợp các nhãn, xung đột ghi ra file để xử lý
            keep = {}
            for s in sets.values():
                for sid, a in s.items():
                    keep.setdefault(sid, a)
        anns = sorted(keep.values(), key=lambda a: (a["s"], a["id"]))
        text = job["x"]
        rec = dict(draft[jid])
        rec.update({
            "gold_skills": [a["n"] for a in anns],
            "annotations": [{"canonical_name": a["n"], "skill_id": a["id"], "evidence": text[a["s"]:a["e"]],
                             "start": a["s"], "end": a["e"]} for a in anns],
            "annotation_status": "human_reviewed", "human_reviewed": True,
            "annotated_by": "Codex (nháp) + người duyệt: " + ", ".join(sorted(done)),
            "review_notes": " | ".join(f"{n}: {reviews[n][jid].get('note')}" for n in sorted(done) if reviews[n][jid].get("note")),
        })
        rows.append(rec)
    summary = {"reviewers": sorted(reviews), "jobs_total": len(jobs), "jobs_reviewed": len(rows),
               "jobs_reviewed_by": {n: sum(1 for j in jobs if rv.get(j, {}).get("done")) for n, rv in reviews.items()},
               "holdout_reviewed": sum(1 for r in rows if jobs[r["job_id"]]["sp"] == "holdout"),
               "conflicting_labels": len(conflicts), "prefer": prefer, "kappa": pairs}
    return rows, conflicts, summary


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", default=sorted(glob.glob(str(EVAL / "reviews/*.json"))))
    ap.add_argument("--prefer", help="tên người duyệt được ưu tiên khi hai người quyết định khác nhau")
    ap.add_argument("--out", default=str(EVAL / "gold_jobs.reviewed.jsonl"))
    a = ap.parse_args(argv)
    if not a.files:
        print("Chưa có file nào trong data/evaluation/reviews/.")
        return 1
    rows, conflicts, summary = merge(load_reviews(a.files), a.prefer)
    out = Path(a.out)
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    cpath = out.with_name("review_conflicts.csv")
    with cpath.open("w", encoding="utf-8-sig", newline="") as f:
        cols = sorted({k for c in conflicts for k in c}, key=lambda k: (not k.startswith(("job", "skill", "canon")), k))
        w = csv.DictWriter(f, fieldnames=cols or ["job_id", "skill_id", "canonical_name"])
        w.writeheader(); w.writerows(conflicts)
    out.with_name("review_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print(f"\nĐã ghi {out} ({len(rows)} tin), {cpath} ({len(conflicts)} nhãn xung đột).")
    print(f"Đánh giá: python -m src.parser evaluate --gold {out} --subset holdout --output-dir reports/skill_extraction/holdout")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
