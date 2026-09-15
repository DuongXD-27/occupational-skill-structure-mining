import os
import csv
import json
import time
import random
import hashlib
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

# Headers with realistic User-Agent
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
    
    # Reset/initialize JSONL file
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        pass
        
    # Reset/initialize CSV log file with required header (Schema v1 - Section 15)
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
    job_targets = []  # list of tuples: (url, source_job_id)
    seen_urls = set()
    
    print("Collecting seed URLs...")
    for seed_url in SEED_URLS:
        print(f"Fetching listing page: {seed_url}")
        try:
            res = requests.get(seed_url, headers=HEADERS, timeout=15)
            time.sleep(random.uniform(1.5, 2.5))
            if res.status_code != 200:
                print(f"Failed to fetch seed {seed_url}, status: {res.status_code}")
                continue
                
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select(".job-card")
            print(f"Found {len(cards)} job cards on {seed_url}")
            
            for card in cards:
                slug = card.get("data-search--job-selection-job-slug-value")
                job_key = card.get("data-job-key")
                if slug:
                    detail_url = f"https://itviec.com/it-jobs/{slug}"
                    if detail_url not in seen_urls:
                        seen_urls.add(detail_url)
                        job_targets.append((detail_url, job_key))
        except Exception as e:
            print(f"Error fetching seed {seed_url}: {e}")
            
    print(f"Total unique detail URLs collected: {len(job_targets)}")
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
    
    # 1. Parse JSON-LD if available
    json_ld_data = {}
    json_ld_elem = soup.find("script", type="application/ld+json")
    if json_ld_elem and json_ld_elem.string:
        try:
            json_ld_data = json.loads(json_ld_elem.string)
        except Exception:
            pass

    # 2. Extract job_id (deterministic hash)
    job_id = hashlib.sha256(url.encode()).hexdigest()[:16]
    
    # 3. Extract source_job_id
    if not source_job_id and isinstance(json_ld_data.get("identifier"), dict):
        source_job_id = str(json_ld_data.get("identifier", {}).get("value"))
        
    # 4. Extract raw_job_title
    raw_job_title = json_ld_data.get("title")
    if not raw_job_title:
        h1 = soup.select_one("h1")
        raw_job_title = h1.get_text(strip=True) if h1 else None
    raw_job_title = clean_text(raw_job_title)
    
    # 5. Extract company
    company = None
    if isinstance(json_ld_data.get("hiringOrganization"), dict):
        company = json_ld_data.get("hiringOrganization", {}).get("name")
    if not company:
        comp_elem = soup.select_one(".employer-name, .job-details__sub-title, .job-header-info a")
        company = comp_elem.get_text(strip=True) if comp_elem else None
    company = clean_text(company)
    
    # 6. Extract raw_location
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
    
    # 7. Extract posted_date (YYYY-MM-DD)
    posted_date = json_ld_data.get("datePosted")
    if posted_date and len(posted_date) >= 10:
        posted_date = posted_date[:10]
    else:
        posted_date = None
        
    # 8. Extract raw_experience
    raw_experience = None
    exp_badge = soup.select_one(".preview-header-item")
    if exp_badge:
        exp_text = exp_badge.get_text(strip=True)
        if exp_text:
            raw_experience = clean_text(exp_text)

    # 9. Extract salary_raw
    salary_raw = None
    sal_elem = soup.select_one(".salary")
    if sal_elem:
        sal_text = sal_elem.get_text(strip=True)
        if "sign in" not in sal_text.lower():
            salary_raw = sal_text
    salary_raw = clean_text(salary_raw)

    # 10. Extract job_description & job_requirements
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

    # Fallback to JSON-LD description if job_description is missing
    if not job_description and json_ld_data.get("description"):
        desc_soup = BeautifulSoup(json_ld_data.get("description"), "html.parser")
        job_description = desc_soup.get_text(separator="\n", strip=True)
        
    job_description = clean_text(job_description)
    job_requirements = clean_text(job_requirements)

    # Validate mandatory schema v1 rule:
    # "Ensure every row has raw_job_title and at least one of job_description or job_requirements is non-empty."
    if not raw_job_title or (not job_description and not job_requirements):
        log_crawl_result(
            source_url=url,
            status="FAILURE",
            http_status=res.status_code,
            error_type="VALIDATION_ERROR",
            error_message="Missing mandatory raw_job_title or description/requirements"
        )
        return None

    # Construct complete DATA SCHEMA V1 record
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
    print(f"\nStarting crawler. Target: {TARGET_MIN_RECORDS} to {TARGET_MAX_RECORDS} jobs...")
    
    for idx, (url, source_job_id) in enumerate(job_targets, 1):
        if len(valid_records) >= TARGET_MAX_RECORDS:
            print(f"Reached upper target limit of {TARGET_MAX_RECORDS} jobs. Stopping.")
            break
            
        print(f"[{idx}/{len(job_targets)}] Crawling detail page: {url}")
        
        try:
            record = parse_job_detail(url, source_job_id)
            if record:
                valid_records.append(record)
                # Append to JSONL file
                with open(OUTPUT_JSONL, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                print(f"  -> Successfully saved record #{len(valid_records)} ({record['raw_job_title']})")
            else:
                print("  -> Skipped/Failed record.")
        except Exception as e:
            print(f"  -> Exception while parsing {url}: {e}")
            log_crawl_result(
                source_url=url,
                status="FAILURE",
                http_status=None,
                error_type="PARSE_ERROR",
                error_message=str(e)
            )
            
        # Random delay between requests (1.5s - 2.5s) as required
        time.sleep(random.uniform(1.5, 2.5))
        
    print("\nCrawling complete!")
    print(f"Total valid jobs saved to {OUTPUT_JSONL}: {len(valid_records)}")
    print(f"Crawl log written to {OUTPUT_LOG_CSV}")
    
    if len(valid_records) < TARGET_MIN_RECORDS:
        print(f"WARNING: Total valid jobs ({len(valid_records)}) is below target minimum ({TARGET_MIN_RECORDS}).")


if __name__ == "__main__":
    main()
