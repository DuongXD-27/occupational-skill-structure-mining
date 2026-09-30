"""
Main CLI entrypoint for the Data & AI Job Crawler.
Supports CLI arguments for output data, logs, and max job limit.
Maintains in-memory deduplication and adheres strictly to DATA SCHEMA V1.
Outputs full summary metrics upon completion.
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from src.crawler.fetcher import PoliteFetcher
from src.crawler.listing import DEFAULT_SEED_URLS, ListingCrawler
from src.crawler.parser import parse_job_html

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
        parser_version: str = "v0.2",
        delay_min: float = 1.5,
        delay_max: float = 2.5,
        seed_urls: Optional[List[str]] = None,
    ):
        self.output_data = output_data
        self.output_log = output_log
        self.max_jobs = max_jobs
        self.parser_version = parser_version
        self.fetcher = PoliteFetcher(delay_min=delay_min, delay_max=delay_max)
        self.listing = ListingCrawler(self.fetcher, seed_urls=seed_urls)

        # In-memory deduplication sets
        self.seen_urls: Set[str] = set()
        self.seen_job_ids: Set[str] = set()

        # Metrics tracking
        self.saved_records_count = 0
        self.failed_requests_count = 0

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
                "ITviec",
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

        job_targets = self.listing.iter_job_targets(max_jobs=self.max_jobs)

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
                is_valid, record, val_err = parse_job_html(
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

        self.print_summary()


def parse_args():
    parser = argparse.ArgumentParser(
        description="ITviec Data & AI Job Crawler - Capstone Project 2026"
    )
    parser.add_argument(
        "--output-data",
        type=str,
        default="data/pilot/jobs_pilot.jsonl",
        help="Đường dẫn file đầu ra JSONL (mặc định: data/pilot/jobs_pilot.jsonl)",
    )
    parser.add_argument(
        "--output-log",
        type=str,
        default="data/pilot/crawl_log.csv",
        help="Đường dẫn file nhật ký crawl CSV (mặc định: data/pilot/crawl_log.csv)",
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
        default="v0.2",
        help="Phiên bản parser gán nhãn trong log và record (mặc định: v0.2)",
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
    runner = CrawlerRunner(
        output_data=args.output_data,
        output_log=args.output_log,
        max_jobs=args.max_jobs,
        parser_version=args.parser_version,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
    )
    runner.run()


if __name__ == "__main__":
    main()
