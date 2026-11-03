"""
TopCV — nguồn thứ hai (quyết định 2026-11-03, docs/decisions/integration_decisions.md F.1).

Cấu trúc trang khảo sát ngày 2026-11-03:
- Trang tìm kiếm: https://www.topcv.vn/tim-viec-lam-<từ khóa>?page=N, mỗi trang tối đa 50 thẻ
  `div.job-item-search-result[data-job-id]`; link chi tiết ở `h3.title a`; trang kế tiếp ở
  `a[rel=next][data-href]`. Từ khóa không có kết quả trả 0 thẻ.
- Trang chi tiết có hai dạng URL: /viec-lam/<slug>/<id>.html và
  /brand/<công ty>/tuyen-dung/<slug>-j<id>.html. Cả hai có JSON-LD `JobPosting`; mô tả nằm
  trong `description` (HTML) chia bằng <h2> "Mô tả công việc", "Yêu cầu ứng viên",
  "Quyền lợi được hưởng". Khối thông tin đầu trang
  `.box-header-job-list-info__item--content` có cặp tiêu đề/giá trị "Địa điểm",
  "Kinh nghiệm", "Hạn ứng tuyển".

Trường thô giữ nguyên văn bản nguồn như parser ITviec (không strip/gộp khoảng trắng).
Không thu lương, học vấn, phúc lợi hay thông tin cá nhân. `identifier` trong JSON-LD
của TopCV là mã công ty, không phải mã tin, nên `source_job_id` lấy từ URL.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, Generator, List, Optional, Set, Tuple

from bs4 import BeautifulSoup, Tag

from src.crawler.fetcher import AccessBlockedError, PoliteFetcher, detect_block
from src.crawler.parser import element_raw_text, raw_or_none, rendered_text

SOURCE = "TopCV"
BASE_URL = "https://www.topcv.vn"
PARSER_VERSION = "topcv-v0.1"

# Từ khóa cụ thể cho Data/AI (số tin ngày 2026-11-03 trong ngoặc).
SEED_KEYWORDS = [
    "data-analyst",           # 70
    "phan-tich-du-lieu",      # 70 (trùng phần lớn data-analyst)
    "data-engineer",          # 48
    "ky-su-du-lieu",          # 48
    "data-scientist",         # 7
    "khoa-hoc-du-lieu",       # 7
    "data-architect",         # 2
    "analytics-engineer",     # 1
    "big-data",               # 4
    "business-intelligence",  # 18
    "ai-engineer",            # 83
    "tri-tue-nhan-tao",       # 83
    "machine-learning",       # 1
    "machine-learning-engineer",
    "computer-vision",        # 1
    "nlp",                    # 1
    "llm",                    # 14
    "generative-ai",          # 3
]
# Từ khóa rộng: nhiều tin ngoài phạm vi (sales, marketing, nhập liệu...). Chỉ bật khi cần
# thêm ứng viên; cleaner (QR-06) sẽ đánh cờ relevance.
BROAD_KEYWORDS = ["data", "ai"]

DETAIL_ID_PATTERNS = (
    re.compile(r"/viec-lam/[^/?#]+/(\d+)\.html"),
    re.compile(r"/brand/[^/?#]+/tuyen-dung/[^/?#]+-j(\d+)\.html"),
)

DESCRIPTION_HEADINGS = ("mô tả công việc",)
REQUIREMENT_HEADINGS = ("yêu cầu ứng viên", "yêu cầu công việc")


def seed_urls(include_broad: bool = False) -> List[str]:
    keywords = SEED_KEYWORDS + (BROAD_KEYWORDS if include_broad else [])
    return [f"{BASE_URL}/tim-viec-lam-{k}" for k in keywords]


def canonical_detail_url(href: str) -> Optional[str]:
    """Bỏ query/fragment (tham số theo dõi) để một tin luôn có cùng URL và job_id."""
    if not href:
        return None
    url = href.split("#")[0].split("?")[0].strip()
    if url.startswith("/"):
        url = BASE_URL + url
    url = url.replace("https://topcv.vn/", BASE_URL + "/")
    return url if any(p.search(url) for p in DETAIL_ID_PATTERNS) else None


def source_job_id_from_url(url: str) -> Optional[str]:
    for pattern in DETAIL_ID_PATTERNS:
        m = pattern.search(url)
        if m:
            return m.group(1)
    return None


class TopCVListingCrawler:
    """Duyệt các trang tìm kiếm TopCV, trả về (detail_url, source_job_id, card_title)."""

    def __init__(self, fetcher: PoliteFetcher, seed_urls_: Optional[List[str]] = None,
                 include_broad: bool = False, max_pages_per_seed: int = 20):
        self.fetcher = fetcher
        self.seed_urls = seed_urls_ or seed_urls(include_broad)
        self.max_pages_per_seed = max_pages_per_seed
        self.visited_urls: Set[str] = set()
        self.pages_scanned_per_seed: Dict[str, int] = {}
        self.total_discovered_urls = 0
        self.total_duplicates_skipped = 0

    def iter_job_targets(self, max_jobs: Optional[int] = None
                         ) -> Generator[Tuple[str, Optional[str], Optional[str]], None, None]:
        yielded = 0
        for seed in self.seed_urls:
            self.pages_scanned_per_seed[seed] = 0
            page_url: Optional[str] = seed
            print(f"\n[TopCV] Bắt đầu từ khóa: {seed}")
            while page_url and self.pages_scanned_per_seed[seed] < self.max_pages_per_seed:
                status, html, error = self.fetcher.fetch(page_url)
                self.pages_scanned_per_seed[seed] += 1
                reason = detect_block(status, html)
                if reason:
                    raise AccessBlockedError(page_url, status, reason)
                if status != 200 or not html:
                    print(f"[TopCV] Dừng tại {page_url} (HTTP {status}, error={error})")
                    break
                cards, next_url = parse_listing(html)
                new = 0
                for detail_url, title in cards:
                    self.total_discovered_urls += 1
                    if detail_url in self.visited_urls:
                        self.total_duplicates_skipped += 1
                        continue
                    self.visited_urls.add(detail_url)
                    new += 1
                    yield detail_url, source_job_id_from_url(detail_url), title
                    yielded += 1
                    if max_jobs is not None and yielded >= max_jobs:
                        return
                print(f"[TopCV] {page_url}: {len(cards)} thẻ ({new} mới)")
                if not cards:
                    break
                page_url = next_url
                if page_url:
                    self.fetcher.sleep_polite()


def parse_listing(html: str) -> Tuple[List[Tuple[str, Optional[str]]], Optional[str]]:
    """Trả về [(detail_url, card_title)] và URL trang kế tiếp (nếu có)."""
    soup = BeautifulSoup(html, "html.parser")
    cards = []
    for card in soup.select("div.job-item-search-result[data-job-id]"):
        link = card.select_one("h3.title a[href]") or card.select_one("a[href*='/viec-lam/'], a[href*='/tuyen-dung/']")
        url = canonical_detail_url(link.get("href", "")) if link else None
        if not url:
            continue
        # Tiêu đề đầy đủ nằm trong data-original-title (text hiển thị có thể bị cắt ngắn)
        span = link.select_one("[data-original-title]")
        title = raw_or_none(span.get("data-original-title")) if span else None
        cards.append((url, title or raw_or_none(link.get_text())))
    nxt = soup.select_one("a[rel=next][data-href], a[rel=next][href]")
    next_url = None
    if nxt is not None:
        next_url = nxt.get("data-href") or nxt.get("href")
        if next_url and next_url.startswith("/"):
            next_url = BASE_URL + next_url
    return cards, next_url


def _job_posting(soup: BeautifulSoup) -> Dict[str, Any]:
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or script.get_text() or "")
        except (ValueError, TypeError):
            continue
        for item in data if isinstance(data, list) else [data]:
            if isinstance(item, dict) and item.get("@type") == "JobPosting":
                return item
    return {}


def _sections(description_html: str) -> Dict[str, str]:
    """Chia HTML mô tả theo các tiêu đề <h2>/<h3>; giữ nguyên văn bản từng phần."""
    soup = BeautifulSoup(description_html or "", "html.parser")
    out: Dict[str, str] = {}
    headings = soup.find_all(["h2", "h3"])
    for h in headings:
        key = " ".join(h.get_text().split()).lower().rstrip(":")
        parts = []
        for sib in h.next_siblings:
            if isinstance(sib, Tag) and sib.name in ("h2", "h3"):
                break
            parts.append(sib)
        holder = BeautifulSoup("", "html.parser").new_tag("div")
        for part in parts:
            holder.append(part.__copy__() if isinstance(part, Tag) else type(part)(str(part)))
        text = raw_or_none(rendered_text(holder))
        if text and key not in out:
            out[key] = text
    return out


def _header_info(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    info: Dict[str, Optional[str]] = {}
    for item in soup.select(".box-header-job-list-info__item--content"):
        title = item.select_one(".list-info__content__title")
        value = item.select_one(".list-info__content__desc")
        if title and value:
            key = " ".join(title.get_text().split()).lower()
            info.setdefault(key, element_raw_text(value))
    return info


def _location_from_ld(job: Dict[str, Any]) -> Optional[str]:
    locs = job.get("jobLocation")
    regions = []
    for loc in locs if isinstance(locs, list) else [locs]:
        if isinstance(loc, dict) and isinstance(loc.get("address"), dict):
            region = loc["address"].get("addressRegion")
            if region and str(region) not in regions:
                regions.append(str(region))
    return raw_or_none(", ".join(regions)) if regions else None


def parse_topcv_html(
    html: str,
    url: str,
    crawl_timestamp: str,
    parser_version: str = PARSER_VERSION,
    source_job_id: Optional[str] = None,
    fallback_title: Optional[str] = None,
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Bóc trang chi tiết TopCV thành bản ghi 22 trường. Trả (hợp lệ?, bản ghi, lỗi)."""
    soup = BeautifulSoup(html, "html.parser")
    job = _job_posting(soup)
    url = canonical_detail_url(url) or url
    info = _header_info(soup)

    raw_job_title = (element_raw_text(soup.select_one("h1.box-header-job__title, h1"))
                     or raw_or_none(job.get("title")) or raw_or_none(fallback_title))
    org = job.get("hiringOrganization")
    company = raw_or_none(org.get("name")) if isinstance(org, dict) else None
    if not company:
        company = element_raw_text(soup.select_one(".company-name-label a, .company-name, a.company"))
    raw_location = info.get("địa điểm") or _location_from_ld(job)
    raw_experience = info.get("kinh nghiệm")
    posted = job.get("datePosted")
    posted_date = posted[:10] if isinstance(posted, str) and re.match(r"\d{4}-\d{2}-\d{2}", posted) else None

    sections = _sections(job.get("description", ""))
    job_description = next((v for k, v in sections.items() if k in DESCRIPTION_HEADINGS), None)
    job_requirements = next((v for k, v in sections.items() if k in REQUIREMENT_HEADINGS), None)
    if not sections and job.get("description"):
        # Mô tả không có tiêu đề: giữ toàn bộ làm job_description
        job_description = raw_or_none(rendered_text(BeautifulSoup(job["description"], "html.parser")))

    if not raw_job_title:
        return False, None, "Missing mandatory field: raw_job_title"
    if not job_description and not job_requirements:
        return False, None, "Missing both job_description and job_requirements"

    record = {
        "job_id": hashlib.sha256(url.encode()).hexdigest()[:16],
        "source": SOURCE,
        "source_job_id": source_job_id or source_job_id_from_url(url),
        "source_url": url,
        "crawl_timestamp": crawl_timestamp,
        "parser_version": parser_version,
        "raw_job_title": raw_job_title,
        "normalized_job_title": None,
        "company": company,
        "raw_location": raw_location,
        "normalized_location": None,
        "posted_date": posted_date,
        "raw_experience": raw_experience,
        "job_description": job_description,
        "job_requirements": job_requirements,
        "job_text": None,
        "relevance_flag": None,
        "exclusion_reason": None,
        "duplicate_flag": None,
        "duplicate_group_id": None,
        "extracted_skills": None,
        "skill_count": None,
    }
    return True, record, None
