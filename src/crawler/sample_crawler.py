import os
import csv
import json
import time
import random
import hashlib
import sys
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Header HTTP giả lập User-Agent của trình duyệt thực tế
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
}

SEED_URLS = [
    "https://itviec.com/it-jobs/data-analyst",
    "https://itviec.com/it-jobs/data-engineer",
    "https://itviec.com/it-jobs/ai-machine-learning-engineer",
    "https://itviec.com/it-jobs/data-scientist",
]

PARSER_VERSION = "v0.1"
OUTPUT_JSONL = "data/sample/sample_jobs.jsonl"
OUTPUT_LOG_CSV = "data/sample/crawl_log_sample.csv"
TARGET_MIN_RECORDS = 35
TARGET_MAX_RECORDS = 45


def clean_text(text: str) -> str or None:
    if not text:
        return None
    cleaned = " ".join(text.split())
    return cleaned if cleaned else None


def init_files():
    os.makedirs("data/sample", exist_ok=True)
    os.makedirs("src/scraper", exist_ok=True)
    
    # Khởi tạo/làm rỗng file JSONL
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        pass
        
    # Khởi tạo file log CSV với header chuẩn theo Schema §15
    with open(OUTPUT_LOG_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "source",
            "source_url",
            "crawl_timestamp",
            "status",
            "http_status",
            "error_type",
            "error_message",
            "parser_version"
        ])


def log_crawl_result(source_url: str, status: str, http_status: int or None = None, error_type: str or None = None, error_message: str or None = None):
    timestamp = datetime.now(timezone.utc).isoformat()
    with open(OUTPUT_LOG_CSV, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ITviec",
            source_url,
            timestamp,
            status,
            http_status if http_status is not None else "",
            error_type if error_type is not None else "",
            error_message if error_message is not None else "",
            PARSER_VERSION
        ])


def collect_job_links():
    job_targets = []  # Danh sách tuple: (url, source_job_id)
    seen_urls = set()
    
    print("Thu thập danh sách URL từ các trang seed...")
    for seed_url in SEED_URLS:
        print(f"Đang tải trang danh sách: {seed_url}")
        try:
            res = requests.get(seed_url, headers=HEADERS, timeout=15)
            time.sleep(random.uniform(1.5, 2.5))
            if res.status_code != 200:
                print(f"Tải seed {seed_url} thất bại, mã trạng thái: {res.status_code}")
                continue
                
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select(".job-card")
            print(f"Tìm thấy {len(cards)} thẻ việc làm trên {seed_url}")
            
            for card in cards:
                slug = card.get("data-search--job-selection-job-slug-value")
                job_key = card.get("data-job-key")
                if slug:
                    detail_url = f"https://itviec.com/it-jobs/{slug}"
                    if detail_url not in seen_urls:
                        seen_urls.add(detail_url)
                        job_targets.append((detail_url, job_key))
        except Exception as e:
            print(f"Lỗi khi tải seed {seed_url}: {e}")
            
    print(f"Tổng số URL chi tiết duy nhất thu thập được: {len(job_targets)}")
    return job_targets


def parse_job_detail(url: str, source_job_id: str or None) -> dict or None:
    res = requests.get(url, headers=HEADERS, timeout=15)
    crawl_timestamp = datetime.now(timezone.utc).isoformat()
    
    if res.status_code != 200:
        log_crawl_result(
            source_url=url,
            status="FAILURE",
            http_status=res.status_code,
            error_type="HTTP_ERROR",
            error_message=f"HTTP status {res.status_code}"
        )
        return None
        
    soup = BeautifulSoup(res.text, "html.parser")
    
    # 1. Trích xuất khối JSON-LD nếu có
    json_ld_data = {}
    json_ld_elem = soup.find("script", type="application/ld+json")
    if json_ld_elem and json_ld_elem.string:
        try:
            json_ld_data = json.loads(json_ld_elem.string)
        except Exception:
            pass

    # 2. Trích xuất job_id (mã băm xác định)
    job_id = hashlib.sha256(url.encode()).hexdigest()[:16]
    
    # 3. Trích xuất source_job_id
    if not source_job_id and isinstance(json_ld_data.get("identifier"), dict):
        source_job_id = str(json_ld_data.get("identifier", {}).get("value"))
        
    # 4. Trích xuất raw_job_title
    raw_job_title = json_ld_data.get("title")
    if not raw_job_title:
        h1 = soup.select_one("h1")
        raw_job_title = h1.get_text(strip=True) if h1 else None
    raw_job_title = clean_text(raw_job_title)
    
    # 5. Trích xuất company
    company = None
    if isinstance(json_ld_data.get("hiringOrganization"), dict):
        company = json_ld_data.get("hiringOrganization", {}).get("name")
    if not company:
        comp_elem = soup.select_one(".employer-name, .job-details__sub-title, .job-header-info a")
        company = comp_elem.get_text(strip=True) if comp_elem else None
    company = clean_text(company)
    
    # 6. Trích xuất raw_location
    raw_location = None
    job_loc = json_ld_data.get("jobLocation")
    loc_list = []
    if isinstance(job_loc, list):
        for loc in job_loc:
            if isinstance(loc, dict):
                addr = loc.get("address", {})
                if isinstance(addr, dict) and addr.get("addressLocality"):
                    loc_list.append(addr.get("addressLocality"))
    elif isinstance(job_loc, dict):
        addr = job_loc.get("address", {})
        if isinstance(addr, dict) and addr.get("addressLocality"):
            loc_list.append(addr.get("addressLocality"))
    if loc_list:
        raw_location = ", ".join(loc_list)
    else:
        loc_elem = soup.select_one(".job-header-info .location, [title='Ha Noi'], [title='Ho Chi Minh']")
        if loc_elem:
            raw_location = loc_elem.get_text(strip=True)
    raw_location = clean_text(raw_location)
    
    # 7. Trích xuất posted_date (YYYY-MM-DD)
    posted_date = json_ld_data.get("datePosted")
    if posted_date and len(posted_date) >= 10:
        posted_date = posted_date[:10]
    else:
        posted_date = None
        
    # 8. Trích xuất raw_experience
    raw_experience = None
    exp_badge = soup.select_one(".preview-header-item")
    if exp_badge:
        exp_text = exp_badge.get_text(strip=True)
        if exp_text:
            raw_experience = clean_text(exp_text)

    # 9. Trích xuất salary_raw
    salary_raw = None
    sal_elem = soup.select_one(".salary")
    if sal_elem:
        sal_text = sal_elem.get_text(strip=True)
        if "sign in" not in sal_text.lower():
            salary_raw = sal_text
    salary_raw = clean_text(salary_raw)

    # 10. Trích xuất job_description & job_requirements
    job_description = None
    job_requirements = None
    
    for h2 in soup.find_all("h2"):
        h2_text = h2.get_text(strip=True).lower()
        if any(keyword in h2_text for keyword in ["job description", "mô tả công việc"]):
            parent = h2.find_parent("div")
            if parent:
                text_content = parent.get_text(separator="\n", strip=True)
                lines = [l for l in text_content.split("\n") if l.lower() not in ["job description", "mô tả công việc"]]
                job_description = "\n".join(lines)
        elif any(keyword in h2_text for keyword in ["your skills and experience", "yêu cầu", "skills and experience"]):
            parent = h2.find_parent("div")
            if parent:
                text_content = parent.get_text(separator="\n", strip=True)
                lines = [l for l in text_content.split("\n") if l.lower() not in ["your skills and experience", "yêu cầu", "skills and experience"]]
                job_requirements = "\n".join(lines)

    # Dự phòng sang description của JSON-LD nếu job_description bị thiếu
    if not job_description and json_ld_data.get("description"):
        desc_soup = BeautifulSoup(json_ld_data.get("description"), "html.parser")
        job_description = desc_soup.get_text(separator="\n", strip=True)
        
    job_description = clean_text(job_description)
    job_requirements = clean_text(job_requirements)

    # Kiểm tra quy tắc bắt buộc của Schema v1:
    # "Phải có raw_job_title và ít nhất một trong hai trường job_description hoặc job_requirements không rỗng."
    if not raw_job_title or (not job_description and not job_requirements):
        log_crawl_result(
            source_url=url,
            status="FAILURE",
            http_status=res.status_code,
            error_type="VALIDATION_ERROR",
            error_message="Missing mandatory raw_job_title or description/requirements"
        )
        return None

    # Khởi tạo bản ghi hoàn chỉnh theo DATA SCHEMA
    record = {
        "job_id": job_id,
        "source": "ITviec",
        "source_job_id": source_job_id if source_job_id else None,
        "source_url": url,
        "crawl_timestamp": crawl_timestamp,
        "parser_version": PARSER_VERSION,
        "raw_job_title": raw_job_title,
        "normalized_job_title": None,
        "company": company,
        "raw_location": raw_location,
        "normalized_location": None,
        "posted_date": posted_date,
        "raw_experience": raw_experience,
        "experience_min_years": None,
        "experience_max_years": None,
        "education": None,
        "job_description": job_description,
        "job_requirements": job_requirements,
        "job_text": None,
        "salary_raw": salary_raw,
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "relevance_flag": None,
        "exclusion_reason": None,
        "duplicate_flag": None,
        "duplicate_group_id": None,
        "extracted_skills": None,
        "skill_count": None
    }
    
    log_crawl_result(
        source_url=url,
        status="SUCCESS",
        http_status=200,
        error_type=None,
        error_message=None
    )
    return record


def main():
    init_files()
    job_targets = collect_job_links()
    
    valid_records = []
    print(f"\nBắt đầu thu thập. Mục tiêu: từ {TARGET_MIN_RECORDS} đến {TARGET_MAX_RECORDS} tin...")
    
    for idx, (url, source_job_id) in enumerate(job_targets, 1):
        if len(valid_records) >= TARGET_MAX_RECORDS:
            print(f"Đã đạt giới hạn mục tiêu {TARGET_MAX_RECORDS} tin. Dừng thu thập.")
            break
            
        print(f"[{idx}/{len(job_targets)}] Đang thu thập trang chi tiết: {url}")
        
        try:
            record = parse_job_detail(url, source_job_id)
            if record:
                valid_records.append(record)
                # Ghi nối vào file JSONL
                with open(OUTPUT_JSONL, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                print(f"  -> Lưu thành công bản ghi #{len(valid_records)} ({record['raw_job_title']})")
            else:
                print("  -> Bản ghi bị bỏ qua hoặc thất bại.")
        except Exception as e:
            print(f"  -> Lỗi ngoại lệ khi bóc tách {url}: {e}")
            log_crawl_result(
                source_url=url,
                status="FAILURE",
                http_status=None,
                error_type="PARSE_ERROR",
                error_message=str(e)
            )
            
        # Thời gian chờ ngẫu nhiên giữa các request (1.5s - 2.5s) theo yêu cầu
        time.sleep(random.uniform(1.5, 2.5))
        
    print("\nThu thập hoàn tất!")
    print(f"Tổng số tin hợp lệ đã lưu vào {OUTPUT_JSONL}: {len(valid_records)}")
    print(f"Nhật ký crawl đã ghi vào {OUTPUT_LOG_CSV}")
    
    if len(valid_records) < TARGET_MIN_RECORDS:
        print(f"CẢNH BÁO: Số tin hợp lệ ({len(valid_records)}) thấp hơn mục tiêu tối thiểu ({TARGET_MIN_RECORDS}).")


if __name__ == "__main__":
    main()
