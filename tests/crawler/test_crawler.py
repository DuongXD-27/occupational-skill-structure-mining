"""Kiểm thử offline cho crawler ITviec (không gửi request thật)."""

import json

import pytest

from src.crawler import fetcher as fetcher_mod
from src.crawler.fetcher import AccessBlockedError, PoliteFetcher, detect_block
from src.crawler.main import CrawlerRunner
from src.crawler.parser import parse_job_html

SCHEMA_22 = (
    "job_id source source_job_id source_url crawl_timestamp parser_version raw_job_title "
    "normalized_job_title company raw_location normalized_location posted_date raw_experience "
    "job_description job_requirements job_text relevance_flag exclusion_reason "
    "duplicate_flag duplicate_group_id extracted_skills skill_count"
).split()

DETAIL_HTML = """<html><body>
<h1>  Data Analyst  (Power BI,   SQL)
</h1>
<div class="job-header-info"><a>  ACME   Corp </a></div>
<div class="itag"> At office </div>
<div class="itag">  3+ years of   experience </div>
<div class="sec"><h2>Job description</h2>
<ul><li>Build   dashboards</li>
<li>Own KPI   reports</li></ul></div>
<div class="sec"><h2>Your skills and experience</h2>
<p>Python,  SQL</p></div>
</body></html>"""


def test_record_has_22_fields_and_raw_text_unchanged():
    ok, rec, err = parse_job_html(DETAIL_HTML, "https://itviec.com/it-jobs/x-1", "2026-10-01T00:00:00+00:00", "v0.3")
    assert ok, err
    assert list(rec) == SCHEMA_22
    assert rec["raw_job_title"] == "  Data Analyst  (Power BI,   SQL)\n"
    assert rec["company"] == "  ACME   Corp "
    assert rec["raw_experience"] == "  3+ years of   experience "
    assert "Build   dashboards" in rec["job_description"]
    assert "Job description" not in rec["job_description"]
    assert rec["job_requirements"].strip() == "Python,  SQL"


def test_missing_text_is_rejected():
    ok, rec, err = parse_job_html("<h1>Data Engineer</h1>", "https://itviec.com/it-jobs/y", "t", "v0.3")
    assert not ok and rec is None and "job_description" in err


@pytest.mark.parametrize("status", [401, 403, 503])
def test_block_status_detected(status):
    assert detect_block(status, "") == f"HTTP {status}"


def test_challenge_page_detected():
    assert detect_block(200, "<title>Just a moment...</title>") is not None
    assert detect_block(200, "<h1>Data Analyst</h1>") is None


class _Resp:
    def __init__(self, status, text=""):
        self.status_code, self.text = status, text


def test_429_status_kept_after_retries(monkeypatch):
    f = PoliteFetcher()
    monkeypatch.setattr(f.session, "get", lambda url, timeout: _Resp(429))
    monkeypatch.setattr(fetcher_mod.time, "sleep", lambda s: None)
    status, html, err = f.fetch("https://x", max_retries=1)
    assert status == 429 and html is None and "429" in err


class _FakeListing:
    pages_scanned_per_seed, total_discovered_urls, total_duplicates_skipped = {}, 0, 0

    def __init__(self, urls):
        self.urls = urls
        self.max_jobs_arg = "unset"

    def iter_job_targets(self, max_jobs=None):
        self.max_jobs_arg = max_jobs
        for u in self.urls:
            yield u, None, None


class _FakeFetcher:
    def __init__(self, responses):
        self.responses = responses

    def fetch(self, url):
        return self.responses[url]

    def sleep_polite(self):
        pass


def _runner(tmp_path, urls, responses, max_jobs=None):
    r = CrawlerRunner(str(tmp_path / "out.jsonl"), str(tmp_path / "log.csv"), max_jobs=max_jobs)
    r.listing = _FakeListing(urls)
    r.fetcher = _FakeFetcher(responses)
    return r


def test_max_jobs_counts_saved_records_not_targets(tmp_path):
    urls = [f"https://itviec.com/it-jobs/j{i}" for i in range(3)]
    responses = {urls[0]: (404, "", None), urls[1]: (200, DETAIL_HTML, None), urls[2]: (200, DETAIL_HTML, None)}
    r = _runner(tmp_path, urls, responses, max_jobs=2)
    r.run()
    assert r.listing.max_jobs_arg is None
    assert r.saved_records_count == 2


def test_crawl_stops_when_blocked(tmp_path):
    urls = [f"https://itviec.com/it-jobs/j{i}" for i in range(3)]
    responses = {urls[0]: (200, DETAIL_HTML, None), urls[1]: (403, "", None), urls[2]: (200, DETAIL_HTML, None)}
    r = _runner(tmp_path, urls, responses)
    r.run()
    assert isinstance(r.blocked, AccessBlockedError)
    assert r.saved_records_count == 1
    lines = (tmp_path / "out.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 and list(json.loads(lines[0])) == SCHEMA_22
