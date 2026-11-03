"""
Gộp các đợt thu (ITviec, TopCV, nhiều ngày) thành một file raw cho cleaner.

Theo quyết định 2026-11-03 (integration_decisions F.7):
- Chỉ giữ tin có crawl_timestamp trong khung quan sát 2026-09-30 → 2026-11-23 (tính cả hai đầu).
- Cùng source_url thu nhiều lần thì giữ bản thu sớm nhất.
- Không sửa nội dung bản ghi; các cột schema cũ toàn null (bản pilot v0.2) do cleaner xử lý.

    python scripts/combine_raw.py data/pilot/jobs_pilot.jsonl data/raw/itviec/*.jsonl data/raw/topcv/*.jsonl \
        --output data/raw/jobs_raw.jsonl
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import sys
from datetime import date, datetime
from pathlib import Path

WINDOW_START = date(2026, 9, 30)
WINDOW_END = date(2026, 11, 23)


def crawl_date(value: str) -> date:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()


def combine(paths, start=WINDOW_START, end=WINDOW_END):
    kept: dict[str, dict] = {}
    stats = collections.Counter()
    for path in paths:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            stats["read"] += 1
            try:
                day = crawl_date(rec["crawl_timestamp"])
            except (KeyError, TypeError, ValueError):
                stats["bad_timestamp"] += 1
                continue
            if not (start <= day <= end):
                stats["outside_window"] += 1
                continue
            url = rec.get("source_url")
            old = kept.get(url)
            if old is None:
                kept[url] = rec
            else:
                stats["same_url_later_crawl"] += 1
                if str(rec["crawl_timestamp"]) < str(old["crawl_timestamp"]):
                    kept[url] = rec
    rows = sorted(kept.values(), key=lambda r: (str(r["crawl_timestamp"]), r["source_url"]))
    ids = collections.Counter(r["job_id"] for r in rows)
    clash = [k for k, n in ids.items() if n > 1]
    if clash:
        raise ValueError(f"job_id bị trùng giữa các URL khác nhau: {clash[:5]}")
    stats.update(collections.Counter(f"kept_{r['source']}" for r in rows))
    return rows, stats


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="Các file JSONL của từng đợt thu (hỗ trợ glob)")
    ap.add_argument("--output", default="data/raw/jobs_raw.jsonl")
    ap.add_argument("--start", type=date.fromisoformat, default=WINDOW_START)
    ap.add_argument("--end", type=date.fromisoformat, default=WINDOW_END)
    args = ap.parse_args(argv)
    paths = sorted({p for pattern in args.inputs for p in (glob.glob(pattern) or [pattern])})
    rows, stats = combine(paths, args.start, args.end)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({"inputs": paths, "output": str(out), "window": [str(args.start), str(args.end)],
                      "records": len(rows), **stats}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
