"""Tải lại vài trang tin ITviec để tìm chỗ trang hiển thị địa điểm và kinh nghiệm (sửa crawler).

Crawler hiện không lấy được địa điểm ở 29% tin (JSON-LD ghi "Not Available") và không lấy được
kinh nghiệm ở tin nào (report/main.tex §3.6). Script này chọn vài tin thiếu địa điểm và vài tin có
địa điểm, tải lại trang (lịch sự, dừng ngay nếu bị chặn), lưu HTML vào data/raw/html_samples/
(không commit) và in một bản tóm tắt NGẮN để dán lại cho người sửa crawler: khối jobLocation và các
khoá liên quan kinh nghiệm trong JSON-LD, cùng các đoạn chữ ngắn trên trang có tên thành phố hoặc
có mẫu kinh nghiệm, kèm đường dẫn thẻ HTML chứa chúng.

    python scripts/inspect_itviec_pages.py                       # 4 tin thiếu địa điểm + 2 tin có
    python scripts/inspect_itviec_pages.py --n-missing 6 --n-ok 2
    python scripts/inspect_itviec_pages.py --url https://itviec.com/it-jobs/...   # tin cụ thể

Kết quả: data/raw/html_samples/<job_id>.html và data/raw/html_samples/report.json.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CITY_RE = re.compile(
    r"\b(h[aà] n[oộ]i|ha noi|h[oồ] ch[ií] minh|ho chi minh|hcm|tp\.? ?hcm|[dđ][aà] n[aẵ]ng|da nang|"
    r"c[aầ]n th[oơ]|h[aả]i ph[oò]ng|remote|b[iì]nh d[uư][oơ]ng|[dđ][oồ]ng nai)\b",
    re.IGNORECASE,
)
EXP_RE = re.compile(
    r"(\d+\s*\+?\s*(?:-\s*\d+\s*)?(?:years?|yrs?|năm)\b|kinh nghi[eệ]m|experience|"
    r"\b(?:intern|fresher|junior|middle|senior|lead|manager)\b)",
    re.IGNORECASE,
)
MISSING = {None, "", "Not Available"}
MAX_SNIPPET = 140


def css_path(el: Tag, depth: int = 4) -> str:
    """Đường dẫn thẻ ngắn gọn: tên thẻ kèm class/id/data-* của tối đa `depth` tổ tiên."""
    parts = []
    while el is not None and isinstance(el, Tag) and el.name not in ("html", "body") and len(parts) < depth:
        bits = el.name
        if el.get("id"):
            bits += "#" + el["id"]
        if el.get("class"):
            bits += "." + ".".join(el["class"][:3])
        data = [k for k in el.attrs if k.startswith("data-")][:2]
        if data:
            bits += "[" + ",".join(data) + "]"
        parts.append(bits)
        el = el.parent
    return " < ".join(parts)


def json_ld_postings(soup: BeautifulSoup) -> list[dict]:
    out = []
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or s.get_text() or "")
        except (json.JSONDecodeError, TypeError):
            continue
        items = data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []
        out += [d for d in items if isinstance(d, dict) and d.get("@type") == "JobPosting"]
    return out


def short_text_hits(soup: BeautifulSoup, pattern: re.Pattern, limit: int = 12) -> list[dict]:
    """Các đoạn chữ ngắn (dưới 140 ký tự) khớp mẫu, bỏ qua script/style và các đoạn văn dài."""
    hits, seen = [], set()
    for node in soup.find_all(string=True):
        if not isinstance(node, NavigableString) or node.parent.name in ("script", "style", "noscript"):
            continue
        text = " ".join(node.split())
        if not text or len(text) > MAX_SNIPPET or not pattern.search(text):
            continue
        key = (text, css_path(node.parent, 2))
        if key in seen:
            continue
        seen.add(key)
        hits.append({"text": text, "path": css_path(node.parent)})
        if len(hits) >= limit:
            break
    return hits


def analyze_html(html: str) -> dict:
    """Tóm tắt những gì cần để sửa extract_location và extract_raw_experience."""
    soup = BeautifulSoup(html, "html.parser")
    postings = json_ld_postings(soup)
    jp = postings[0] if postings else {}
    exp_keys = {k: jp[k] for k in jp if "experience" in k.lower() or "qualification" in k.lower()}
    return {
        "jsonld_found": bool(postings),
        "jsonld_jobLocation": jp.get("jobLocation"),
        "jsonld_jobLocationType": jp.get("jobLocationType"),
        "jsonld_experience_keys": {k: (v if len(json.dumps(v, ensure_ascii=False)) < 300 else "<dài>") for k, v in exp_keys.items()},
        "location_like_text": short_text_hits(soup, CITY_RE),
        "experience_like_text": short_text_hits(soup, EXP_RE),
    }


def pick(raw_path: Path, n_missing: int, n_ok: int) -> list[dict]:
    """Ưu tiên tin của đợt thu gần nhất (còn đăng nhiều khả năng nhất)."""
    rows = [json.loads(l) for l in raw_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows.sort(key=lambda r: r.get("crawl_timestamp") or "", reverse=True)
    miss = [r for r in rows if r.get("raw_location") in MISSING][:n_missing]
    ok = [r for r in rows if r.get("raw_location") not in MISSING][:n_ok]
    return miss + ok


def main() -> None:
    from src.crawler.fetcher import PoliteFetcher, detect_block

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw", default=str(ROOT / "data/raw/jobs_raw.jsonl"))
    ap.add_argument("--n-missing", type=int, default=4)
    ap.add_argument("--n-ok", type=int, default=2)
    ap.add_argument("--url", action="append", default=[], help="tải đúng URL này (có thể lặp lại)")
    ap.add_argument("--out", default=str(ROOT / "data/raw/html_samples"))
    a = ap.parse_args()

    targets = [{"job_id": f"url{i}", "source_url": u, "raw_location": "?"} for i, u in enumerate(a.url)]
    if not targets:
        targets = pick(Path(a.raw), a.n_missing, a.n_ok)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    fetcher = PoliteFetcher(delay_min=2.0, delay_max=3.5)
    report = []
    for i, t in enumerate(targets):
        if i:
            fetcher.sleep_polite()
        status, html, err = fetcher.fetch(t["source_url"], max_retries=1)
        reason = detect_block(status, html)
        if reason:
            print(f"DỪNG: trang chặn truy cập ({reason}). Không thử vượt chặn.")
            break
        entry = {"job_id": t["job_id"], "url": t["source_url"], "crawler_raw_location": t.get("raw_location"),
                 "http_status": status, "error": err}
        if html and status == 200:
            (out / f"{t['job_id']}.html").write_text(html, encoding="utf-8")
            entry.update(analyze_html(html))
        report.append(entry)
        print(f"[{i + 1}/{len(targets)}] HTTP {status} {t['source_url']}")
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nĐã lưu {out / 'report.json'}. Gửi lại nội dung file này (không cần gửi file .html).")


if __name__ == "__main__":
    main()
