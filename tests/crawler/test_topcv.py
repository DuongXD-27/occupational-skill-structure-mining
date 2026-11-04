"""Kiểm thử offline cho TopCV. HTML mẫu là bản tự dựng theo cấu trúc trang khảo sát
ngày 2026-11-03 (không chép nội dung tin thật)."""

import json
import sys
from pathlib import Path

from src.crawler import topcv
from src.crawler.main import CrawlerRunner
from tests.crawler.test_crawler import SCHEMA_22

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import combine_raw  # noqa: E402

LISTING = """<html><body>
<div class="job-item-search-result bg-highlight" data-job-id="111">
  <h3 class="title"><a href="https://www.topcv.vn/viec-lam/data-analyst-ha-noi/111.html?ta_source=JobSearchList&u_sr_id=x">
    <span data-original-title="Data Analyst (SQL, Power BI) - Hà Nội">Data Analyst (SQL, Po…</span></a></h3>
</div>
<div class="job-item-search-result" data-job-id="222">
  <h3 class="title"><a href="https://www.topcv.vn/brand/acme/tuyen-dung/ai-engineer-llm-j222.html?u_sr_id=y">
    <span data-original-title="AI Engineer (LLM)">AI Engineer (LLM)</span></a></h3>
</div>
<div class="job-item-search-result" data-job-id="333"><h3 class="title"><a href="https://www.topcv.vn/cong-ty/acme/1.html">Công ty</a></h3></div>
<nav class="box-pagination"><ul class="pagination"><li><a data-href="https://www.topcv.vn/tim-viec-lam-data-analyst?page=2" rel="next"></a></li></ul></nav>
</body></html>"""

JOB_LD = {
    "@context": "http://schema.org/", "@type": "JobPosting",
    "title": "Data Analyst (SQL, Power BI) - Hà Nội",
    "description": "<h2>Mô tả công việc</h2>\n<ul><li>Xây dựng  dashboard Power BI</li><li>Viết SQL</li></ul>"
                   "<h2>Yêu cầu ứng viên</h2>\n<ul><li>2 năm kinh nghiệm Python</li></ul>"
                   "<h2>Quyền lợi được hưởng</h2><p>Lương tháng 13</p>",
    "identifier": {"@type": "PropertyValue", "name": "Công ty ACME", "value": 999},
    "datePosted": "2026-10-14",
    "hiringOrganization": {"@type": "Organization", "name": "Công ty ACME"},
    "jobLocation": {"@type": "Place", "address": {"addressRegion": "Hà Nội"}},
    "baseSalary": {"currency": "VND"},
}
DETAIL = f"""<html><head><script type="application/ld+json">{json.dumps(JOB_LD, ensure_ascii=False)}</script></head>
<body><h1 class="box-header-job__title">  Data Analyst (SQL, Power BI) - Hà Nội </h1>
<div class="box-header-job-list-info__item--content"><div class="list-info__content__title">Địa điểm</div>
<div class="list-info__content__desc"> Hà Nội </div></div>
<div class="box-header-job-list-info__item--content"><div class="list-info__content__title">Kinh nghiệm</div>
<div class="list-info__content__desc">2 năm</div></div>
</body></html>"""


def test_listing_cards_and_next_page():
    cards, nxt = topcv.parse_listing(LISTING)
    assert cards == [
        ("https://www.topcv.vn/viec-lam/data-analyst-ha-noi/111.html", "Data Analyst (SQL, Power BI) - Hà Nội"),
        ("https://www.topcv.vn/brand/acme/tuyen-dung/ai-engineer-llm-j222.html", "AI Engineer (LLM)"),
    ]
    assert nxt == "https://www.topcv.vn/tim-viec-lam-data-analyst?page=2"
    assert topcv.source_job_id_from_url(cards[1][0]) == "222"


def test_detail_record_22_fields_raw_text_kept():
    url = "https://www.topcv.vn/viec-lam/data-analyst-ha-noi/111.html?ta_source=x"
    ok, rec, err = topcv.parse_topcv_html(DETAIL, url, "2026-11-03T00:00:00+00:00")
    assert ok, err
    assert list(rec) == SCHEMA_22
    assert rec["source"] == "TopCV" and rec["source_job_id"] == "111"
    assert rec["source_url"] == "https://www.topcv.vn/viec-lam/data-analyst-ha-noi/111.html"
    assert rec["raw_job_title"] == "  Data Analyst (SQL, Power BI) - Hà Nội "
    assert rec["raw_location"] == " Hà Nội " and rec["raw_experience"] == "2 năm"
    assert rec["company"] == "Công ty ACME" and rec["posted_date"] == "2026-10-14"
    assert "Xây dựng  dashboard" in rec["job_description"] and "Python" in rec["job_requirements"]
    assert "Lương" not in rec["job_description"] + rec["job_requirements"]


def test_detail_without_text_rejected():
    ok, rec, err = topcv.parse_topcv_html("<h1>Data Engineer</h1>", "https://www.topcv.vn/viec-lam/x/1.html", "t")
    assert not ok and "job_description" in err


class _Fetcher:
    def __init__(self, pages):
        self.pages = pages

    def fetch(self, url):
        return self.pages.get(url, (404, "", None))

    def sleep_polite(self, *a):
        pass


def test_runner_crawls_topcv_and_stops_on_block(tmp_path):
    seed = "https://www.topcv.vn/tim-viec-lam-data-analyst"
    d1 = "https://www.topcv.vn/viec-lam/data-analyst-ha-noi/111.html"
    d2 = "https://www.topcv.vn/brand/acme/tuyen-dung/ai-engineer-llm-j222.html"
    pages = {seed: (200, LISTING, None), d1: (200, DETAIL, None), d2: (403, "", None)}
    r = CrawlerRunner(str(tmp_path / "out.jsonl"), str(tmp_path / "log.csv"), source="topcv",
                      parser_version=topcv.PARSER_VERSION, seed_urls=[seed])
    r.fetcher = r.listing.fetcher = _Fetcher(pages)
    r.run()
    rows = [json.loads(l) for l in (tmp_path / "out.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1 and rows[0]["source"] == "TopCV"
    assert r.blocked is not None and r.blocked.status == 403
    assert "TopCV" in (tmp_path / "log.csv").read_text(encoding="utf-8")


def _rec(url, ts, src="TopCV"):
    rec = dict.fromkeys(SCHEMA_22)
    rec.update(job_id=url[-6:], source=src, source_url=url, crawl_timestamp=ts)
    return rec


def test_combine_keeps_earliest_crawl_inside_window(tmp_path):
    a, b = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    a.write_text("\n".join(json.dumps(r) for r in [
        _rec("https://x/u1aaaa", "2026-10-10T00:00:00+00:00"),
        _rec("https://x/u2bbbb", "2026-09-20T00:00:00+00:00"),        # trước khung
    ]) + "\n", encoding="utf-8")
    b.write_text("\n".join(json.dumps(r) for r in [
        _rec("https://x/u1aaaa", "2026-11-01T00:00:00+00:00"),        # thu lại → bỏ
        _rec("https://x/u3cccc", "2026-11-24T00:00:00+00:00"),        # sau khung
        _rec("https://x/u4dddd", "2026-11-23T16:00:00+00:00", "ITviec"),  # 23:00 giờ VN
    ]) + "\n", encoding="utf-8")
    rows, stats = combine_raw.combine([a, b])
    assert [r["source_url"] for r in rows] == ["https://x/u1aaaa", "https://x/u4dddd"]
    assert rows[0]["crawl_timestamp"].startswith("2026-10-10")
    assert stats["outside_window"] == 2 and stats["same_url_later_crawl"] == 1


def test_window_uses_vietnam_date():
    # 22:10 UTC ngày 29/09 là 05:10 ngày 30/09 ở Việt Nam: vẫn nằm trong khung quan sát
    assert str(combine_raw.crawl_date("2026-09-29T22:10:16+00:00")) == "2026-09-30"
    assert str(combine_raw.crawl_date("2026-11-23T18:00:00+00:00")) == "2026-11-24"
