"""
Listing module for crawling job search pages with dynamic pagination and in-memory deduplication.
Supports both standard keyword pagination (?page=1, 2, 3...) and segment landing pages.
"""

import re
import sys
from typing import Dict, Generator, List, Optional, Set, Tuple
from bs4 import BeautifulSoup
from src.crawler.fetcher import PoliteFetcher

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

DEFAULT_SEED_URLS = [
    "https://itviec.com/it-jobs/data-analyst",
    "https://itviec.com/it-jobs/data-engineer",
    "https://itviec.com/it-jobs/data-scientist",
    "https://itviec.com/it-jobs/ai-machine-learning-engineer",
    "https://itviec.com/it-jobs/business-analyst",
    "https://itviec.com/it-jobs/database-administrator",
    "https://itviec.com/segments/viec-lam-ai-data",
]

JOB_SLUG_PATTERN = re.compile(r"-\d{4}$")


def extract_slug(href_or_slug: str) -> str:
    """Safely extract the clean job slug from any relative or absolute URL."""
    path = href_or_slug.split("?")[0].strip()
    if "/it-jobs/" in path:
        return path.split("/it-jobs/")[-1].strip("/")
    if path.startswith("it-jobs/"):
        return path[len("it-jobs/"):].strip("/")
    return path.strip("/")


class ListingCrawler:
    """Discovers job URLs across seed categories using dynamic pagination."""

    def __init__(
        self,
        fetcher: PoliteFetcher,
        seed_urls: Optional[List[str]] = None,
    ):
        self.fetcher = fetcher
        self.seed_urls = seed_urls or DEFAULT_SEED_URLS
        self.visited_urls: Set[str] = set()

        # Metrics tracking
        self.pages_scanned_per_seed: Dict[str, int] = {}
        self.total_discovered_urls: int = 0
        self.total_duplicates_skipped: int = 0

    def iter_job_targets(
        self,
        max_jobs: Optional[int] = None,
    ) -> Generator[Tuple[str, Optional[str], Optional[str]], None, None]:
        """
        Iterate through seed URLs and pagination pages (?page=1, 2, 3...).
        Stops pagination automatically when no cards exist or HTTP non-200.
        Yields:
            (detail_url, source_job_id, card_title)
        """
        yielded_count = 0

        for seed_url in self.seed_urls:
            page = 1
            self.pages_scanned_per_seed[seed_url] = 0
            print(f"\n[Listing] Bắt đầu duyệt danh mục hạt giống: {seed_url}")

            while True:
                # Segment landing pages do not support ?page query
                if "segments/" in seed_url:
                    page_url = seed_url
                else:
                    page_url = f"{seed_url}?page={page}" if page > 1 else seed_url

                print(f"[Listing] Tải trang {page}: {page_url}")
                status_code, html, error = self.fetcher.fetch(page_url)
                self.pages_scanned_per_seed[seed_url] += 1

                if status_code != 200 or not html:
                    print(f"[Listing] Dừng phân trang tại {page_url} (HTTP {status_code}, error={error})")
                    break

                soup = BeautifulSoup(html, "html.parser")
                cards = soup.select(".job-card")

                if cards:
                    new_cards_found = 0
                    for card in cards:
                        slug = card.get("data-search--job-selection-job-slug-value")
                        job_key = card.get("data-job-key")

                        if not slug:
                            link_tag = card.select_one("a[href*='/it-jobs/']")
                            if link_tag and link_tag.get("href"):
                                slug = extract_slug(str(link_tag.get("href")))

                        if not slug:
                            continue

                        detail_url = f"https://itviec.com/it-jobs/{slug}"
                        self.total_discovered_urls += 1

                        # In-memory deduplication check
                        if detail_url in self.visited_urls:
                            self.total_duplicates_skipped += 1
                            continue

                        self.visited_urls.add(detail_url)
                        new_cards_found += 1

                        card_title = None
                        title_elem = card.select_one("h3 a, a.text-it-black, [data-search--job-selection-job-title-value]")
                        if title_elem:
                            card_title = title_elem.get_text(strip=True)

                        yield (detail_url, job_key, card_title)
                        yielded_count += 1

                        if max_jobs is not None and yielded_count >= max_jobs:
                            print(f"[Listing] Đã thu thập đủ {max_jobs} mục tiêu việc làm duy nhất. Dừng quét danh sách.")
                            return

                    print(f"[Listing] Trang {page}: Tìm thấy {len(cards)} thẻ ({new_cards_found} mới, {len(cards) - new_cards_found} đã trùng).")
                    page += 1
                    self.fetcher.sleep_polite()

                else:
                    # Segment landing page or alternative card layout
                    links_found = 0
                    for a in soup.select("a[href*='/it-jobs/']"):
                        href = a.get("href", "")
                        if "click_source=Navigation" in href or "click_source=Skill" in href:
                            continue
                        slug = extract_slug(href)
                        if JOB_SLUG_PATTERN.search(slug):
                            detail_url = f"https://itviec.com/it-jobs/{slug}"
                            self.total_discovered_urls += 1

                            if detail_url in self.visited_urls:
                                self.total_duplicates_skipped += 1
                                continue

                            self.visited_urls.add(detail_url)
                            links_found += 1

                            card_title = a.get_text(strip=True) or None
                            yield (detail_url, None, card_title)
                            yielded_count += 1

                            if max_jobs is not None and yielded_count >= max_jobs:
                                print(f"[Listing] Đã thu thập đủ {max_jobs} mục tiêu việc làm duy nhất. Dừng quét danh sách.")
                                return

                    if links_found > 0:
                        print(f"[Listing] Trang phân khúc {seed_url}: Thu thập được {links_found} liên kết việc làm mới.")
                    else:
                        print(f"[Listing] Không tìm thấy thêm liên kết việc làm nào trên trang {page}. Kết thúc duyệt hạt giống này.")
                    break
