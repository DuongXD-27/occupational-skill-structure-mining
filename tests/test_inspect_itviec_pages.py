import json

from scripts.inspect_itviec_pages import analyze_html, pick

HTML = """<html><head>
<script type="application/ld+json">{"@type": "JobPosting", "title": "Data Engineer",
 "jobLocation": {"@type": "Place", "address": {"addressLocality": "Not Available", "addressRegion": "Ha Noi"}},
 "experienceRequirements": {"@type": "OccupationalExperienceRequirements", "monthsOfExperience": 36}}</script>
<script>var x = "Ha Noi 3 years";</script></head>
<body><div class="job-header"><span class="ipe-2 text-dark-grey">Toa nha ABC, Cau Giay, Ha Noi</span></div>
<div class="overview" data-testid="exp"><span>3+ years of experience</span></div>
<p>""" + "Long paragraph about Ha Noi " * 20 + """</p></body></html>"""


def test_analyze_html_finds_jsonld_and_short_snippets():
    r = analyze_html(HTML)
    assert r["jsonld_found"]
    assert r["jsonld_jobLocation"]["address"]["addressRegion"] == "Ha Noi"
    assert "experienceRequirements" in r["jsonld_experience_keys"]
    locs = [h["text"] for h in r["location_like_text"]]
    assert "Toa nha ABC, Cau Giay, Ha Noi" in locs
    assert all(len(t) <= 140 for t in locs)          # đoạn văn dài bị bỏ qua
    assert not any("var x" in t for t in locs)       # bỏ qua script
    exp = r["experience_like_text"]
    assert exp[0]["text"] == "3+ years of experience" and "data-testid" in exp[0]["path"]


def test_pick_prefers_latest_crawl(tmp_path):
    rows = [
        {"job_id": "a", "source_url": "u1", "raw_location": "Not Available", "crawl_timestamp": "2026-09-30T00:00:00+00:00"},
        {"job_id": "b", "source_url": "u2", "raw_location": None, "crawl_timestamp": "2026-11-03T00:00:00+00:00"},
        {"job_id": "c", "source_url": "u3", "raw_location": "Ha Noi", "crawl_timestamp": "2026-11-03T00:00:00+00:00"},
    ]
    p = tmp_path / "raw.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows))
    got = [r["job_id"] for r in pick(p, n_missing=1, n_ok=1)]
    assert got == ["b", "c"]
