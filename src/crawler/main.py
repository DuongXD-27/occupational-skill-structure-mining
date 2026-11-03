"""
Main CLI entrypoint for the Data & AI Job Crawler.
Supports CLI arguments for output data, logs, and max job limit.
Maintains in-memory deduplication and writes records in the 22-field schema (docs/data_schema.md).
Outputs full summary metrics upon completion.
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from src.crawler.fetcher import AccessBlockedError, PoliteFetcher, detect_block
from src.crawler.listing import DEFAULT_SEED_URLS, ListingCrawler
from src.crawler.parser import parse_job_html
from src.crawler import topcv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

LOG_HEADER = [
    "source",
    "source_url",
    "crawl_timestamp",
    "status",
    "http_status",
    "error_type",
    "error_message",
    "parser_version",
]


class CrawlerRunner:
    """Orchestrates listing discovery, detail page fetching, parsing, and logging."""

    def __init__(
        self,
        output_data: str,
        output_log: str,
        max_jobs: Optional[int] = None,
        parser_version: str = "v0.3",
        delay_min: float = 1.5,
        delay_max: float = 2.5,
        seed_urls: Optional[List[str]] = None,
        source: str = "itviec",
        include_broad: bool = False,
    ):
        self.output_data = output_data
        self.output_log = output_log
        self.max_jobs = max_jobs
        self.parser_version = parser_version
        self.fetcher = PoliteFetcher(delay_min=delay_min, delay_max=delay_max)
        if source == "topcv":
            self.source_name = topcv.SOURCE
            self.listing = topcv.TopCVListingCrawler(self.fetcher, seed_urls, include_broad=include_broad)
            self.parse = topcv.parse_topcv_html
        elif source == "itviec":
            self.source_name = "ITviec"
            self.listing = ListingCrawler(self.fetcher, seed_urls=seed_urls)
            self.parse = parse_job_html
        else:
            raise ValueError(f"Nguồn không hỗ trợ: {source}")

        # In-memory deduplication sets
        self.seen_urls: Set[str] = set()
        self.seen_job_ids: Set[str] = set()

        # Metrics tracking
        self.saved_records_count = 0
        self.failed_requests_count = 0
        self.blocked: Optional[AccessBlockedError] = None

    def init_storage(self):
        """Prepare output files and write header to log CSV."""
        out_dir = os.path.dirname(self.output_data)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        log_dir = os.path.dirname(self.output_log)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        with open(self.output_log, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(LOG_HEADER)

        with open(self.output_data, "w", encoding="utf-8") as f:
            pass

    def log_result(
        self,
        source_url: str,
        status: str,
        http_status: Optional[int] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        crawl_timestamp: Optional[str] = None,
    ):
        """Append a record to the crawl log CSV according to Schema §15."""
        ts = crawl_timestamp or datetime.now(timezone.utc).isoformat()
        if status == "FAILURE":
            self.failed_requests_count += 1

        with open(self.output_log, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                self.source_name,
                source_url,
                ts,
                status,
                http_status if http_status is not None else "",
                error_type or "",
                error_message or "",
                self.parser_version,
            ])

    def print_summary(self):
        """Print post-run summary metrics as required by project specifications."""
        print("\n" + "=" * 60)
        print("         BÁO CÁO TỔNG KẾT THU THẬP DỮ LIỆU (CRAWL SUMMARY)        ")
        print("=" * 60)
        print("\n1. Số trang danh sách đã quét theo từng URL hạt giống:")
        for seed_url, pages in self.listing.pages_scanned_per_seed.items():
            print(f"   - {seed_url}: {pages} trang")

        print(f"\n2. Tổng số URL chi tiết phát hiện được: {self.listing.total_discovered_urls}")
        print(f"3. Tổng số URL trùng lặp đã bỏ qua: {self.listing.total_duplicates_skipped}")
        print(f"4. Tổng số bản ghi ghi thành công vào dataset ({self.output_data}): {self.saved_records_count}")
        print(f"5. Tổng số yêu cầu thất bại ghi nhận trong log ({self.output_log}): {self.failed_requests_count}")
        print("=" * 60 + "\n")

    def run(self):
        """Execute the crawling workflow."""
        self.init_storage()
        print(f"=== Bắt đầu thu thập dữ liệu việc làm Data & AI ===")
        print(f"Dữ liệu đích: {self.output_data}")
        print(f"Nhật ký crawl: {self.output_log}")
        print(f"Giới hạn số tin: {self.max_jobs or 'Toàn bộ khả dụng (Exhaustive)'}")
        print(f"Phiên bản parser: {self.parser_version}\n")

        # --max-jobs giới hạn số bản ghi lưu được (kiểm tra ở vòng lặp dưới), không giới hạn
        # số URL mục tiêu: một trang chi tiết lỗi không được chiếm chỗ của tin hợp lệ.
        job_targets = self.listing.iter_job_targets()

        try:
            self._crawl(job_targets)
        except AccessBlockedError as exc:
            # Nguồn chặn truy cập (HTTP 401/403/503 hoặc thử thách chống bot):
            # dừng toàn bộ đợt thu thập, không thử vượt qua (source_inspection.md, project_scope §7).
            self.blocked = exc
            print(f"\n[DỪNG] {exc}. Kết thúc đợt thu thập theo quy định nguồn dữ liệu.")
            self.log_result(
                source_url=exc.url,
                status="FAILURE",
                http_status=exc.status,
                error_type="ACCESS_BLOCKED",
                error_message=exc.reason,
            )

        self.print_summary()

    def _crawl(self, job_targets):
        for detail_url, source_job_key, card_title in job_targets:
            if self.max_jobs is not None and self.saved_records_count >= self.max_jobs:
                print(f"\nĐã đạt chỉ tiêu tối đa {self.max_jobs} bản ghi. Kết thúc.")
                break

            # In-memory deduplication check
            if detail_url in self.seen_urls:
                continue
            self.seen_urls.add(detail_url)

            crawl_timestamp = datetime.now(timezone.utc).isoformat()
            status_code, html, net_err = self.fetcher.fetch(detail_url)

            block_reason = detect_block(status_code, html)
            if block_reason:
                raise AccessBlockedError(detail_url, status_code, block_reason)

            if status_code != 200 or not html:
                print(f"[{self.saved_records_count + 1}] THẤT BẠI: {detail_url} (HTTP {status_code}: {net_err})")
                self.log_result(
                    source_url=detail_url,
                    status="FAILURE",
                    http_status=status_code,
                    error_type="HTTP_ERROR",
                    error_message=net_err or f"HTTP status {status_code}",
                    crawl_timestamp=crawl_timestamp,
                )
                self.fetcher.sleep_polite()
                continue

            try:
                is_valid, record, val_err = self.parse(
                    html=html,
                    url=detail_url,
                    crawl_timestamp=crawl_timestamp,
                    parser_version=self.parser_version,
                    source_job_id=source_job_key,
                    fallback_title=card_title,
                )
            except Exception as exc:
                print(f"[{self.saved_records_count + 1}] LỖI PARSER: {detail_url} ({exc})")
                self.log_result(
                    source_url=detail_url,
                    status="FAILURE",
                    http_status=status_code,
                    error_type="PARSE_ERROR",
                    error_message=str(exc),
                    crawl_timestamp=crawl_timestamp,
                )
                self.fetcher.sleep_polite()
                continue

            if not is_valid or not record:
                print(f"[{self.saved_records_count + 1}] KHÔNG ĐẠT SCHEMA: {detail_url} ({val_err})")
                self.log_result(
                    source_url=detail_url,
                    status="FAILURE",
                    http_status=status_code,
                    error_type="VALIDATION_ERROR",
                    error_message=val_err,
                    crawl_timestamp=crawl_timestamp,
                )
                self.fetcher.sleep_polite()
                continue

            job_id = record["job_id"]
            if job_id in self.seen_job_ids:
                print(f"  -> Trùng job_id {job_id}, bỏ qua.")
                continue
            self.seen_job_ids.add(job_id)

            with open(self.output_data, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

            self.saved_records_count += 1
            self.log_result(
                source_url=detail_url,
                status="SUCCESS",
                http_status=200,
                error_type=None,
                error_message=None,
                crawl_timestamp=crawl_timestamp,
            )

            print(
                f"[{self.saved_records_count}] Lưu OK: {record['raw_job_title']} | "
                f"exp={repr(record['raw_experience'])} | {record['company']}"
            )

            self.fetcher.sleep_polite()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Data & AI Job Crawler (ITviec, TopCV) - Capstone Project 2026"
    )
    parser.add_argument(
        "--source",
        choices=("itviec", "topcv"),
        default="itviec",
        help="Nguồn thu thập (mặc định: itviec). TopCV là nguồn thứ hai từ 2026-11-03.",
    )
    parser.add_argument(
        "--include-broad",
        action="store_true",
        help="TopCV: thêm từ khóa rộng 'data', 'ai' (nhiều tin ngoài phạm vi, cleaner sẽ lọc)",
    )
    parser.add_argument(
        "--output-data",
        type=str,
        default=None,
        help="File JSONL đầu ra (mặc định: data/raw/<nguồn>/jobs_<nguồn>_<ngày>.jsonl; "
             "không ghi đè file pilot đã commit)",
    )
    parser.add_argument(
        "--output-log",
        type=str,
        default=None,
        help="File log CSV (mặc định: data/raw/<nguồn>/crawl_log_<nguồn>_<ngày>.csv; "
             "mỗi đợt thu một file theo ngày)",
    )
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=None,
        help="Số lượng tin tối đa cần thu thập (mặc định: None = toàn bộ khả dụng)",
    )
    parser.add_argument(
        "--parser-version",
        type=str,
        default=None,
        help="Phiên bản parser ghi vào log/record (mặc định: ITviec v0.3, TopCV topcv-v0.1)",
    )
    parser.add_argument(
        "--delay-min",
        type=float,
        default=1.5,
        help="Thời gian chờ tối thiểu giữa các request (giây, mặc định: 1.5)",
    )
    parser.add_argument(
        "--delay-max",
        type=float,
        default=2.5,
        help="Thời gian chờ tối đa giữa các request (giây, mặc định: 2.5)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    if args.source == "topcv":
        output_data = args.output_data or f"data/raw/topcv/jobs_topcv_{day}.jsonl"
        output_log = args.output_log or f"data/raw/topcv/crawl_log_topcv_{day}.csv"
        parser_version = args.parser_version or topcv.PARSER_VERSION
    else:
        output_data = args.output_data or f"data/raw/itviec/jobs_itviec_{day}.jsonl"
        output_log = args.output_log or f"data/raw/itviec/crawl_log_itviec_{day}.csv"
        parser_version = args.parser_version or "v0.3"
    runner = CrawlerRunner(
        output_data=output_data,
        output_log=output_log,
        max_jobs=args.max_jobs,
        parser_version=parser_version,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        source=args.source,
        include_broad=args.include_broad,
    )
    runner.run()
    if runner.blocked is not None:
        sys.exit(2)


if __name__ == "__main__":
    main()
