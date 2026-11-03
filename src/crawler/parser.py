"""
Parser module for ITviec job postings.
Emits records in the 22-field schema (docs/data_schema.md). Raw fields
(`raw_job_title`, `company`, `raw_location`, `raw_experience`,
`job_description`, `job_requirements`) keep the text exactly as rendered on the
source page: no trimming or whitespace normalization. Cleanup belongs to the
cleaner's derived fields. Salary and education are not collected (decision
2026-10-04, docs/decisions/integration_decisions.md §B).
"""

import hashlib
import json
import re
from typing import Any, Dict, Optional, Tuple
from bs4 import BeautifulSoup, Comment, NavigableString, Tag

# Working models and non-experience tags to strictly discard
WORKING_MODEL_KEYWORDS = {
    "at office",
    "hybrid",
    "remote",
    "onsite",
    "on-site",
    "work from home",
    "wfh",
    "full-time",
    "full time",
    "part-time",
    "part time",
    "toàn thời gian",
    "bán thời gian",
}

DISCARD_PATTERNS = [
    re.compile(r"^\s*posted\b", re.IGNORECASE),
    re.compile(r"\b(?:days?|hours?|weeks?|months?)\s+ago\b", re.IGNORECASE),
    re.compile(r"\b(?:ngày|giờ|tuần|tháng)\s+trước\b", re.IGNORECASE),
    re.compile(r"\b(?:hà nội|ha noi|hồ chí minh|ho chi minh|đà nẵng|da nang|quận|huyện|district)\b", re.IGNORECASE),
]

# Patterns representing genuine experience requirements
EXPERIENCE_PATTERNS = [
    re.compile(r"\d+\+?\s*(?:-\s*\d+)?\s*(?:years?|năm|tháng|yrs?|yoe)\b", re.IGNORECASE),
    re.compile(r"\b(?:year|years|năm)\s+of\s+experience\b", re.IGNORECASE),
    re.compile(r"\b(?:kinh nghiệm|experience)\b", re.IGNORECASE),
    re.compile(r"^(?:intern|internship|fresher|junior|middle|senior|lead|principal|expert|director|head)(?:\s+(?:level|developer|engineer|analyst))?$", re.IGNORECASE),
]


def clean_text(text: Optional[str]) -> Optional[str]:
    """Collapse whitespace. Use ONLY for matching/validation, never for stored raw values."""
    if not text:
        return None
    cleaned = " ".join(text.split())
    return cleaned if cleaned else None


def raw_or_none(text: Optional[str]) -> Optional[str]:
    """Return the source text unchanged, or None when it holds no visible characters."""
    if text is None:
        return None
    text = str(text)
    return text if text.strip() else None


def element_raw_text(elem: Optional[Tag]) -> Optional[str]:
    """Text of an element as rendered in the HTML, without strip/normalization."""
    if elem is None:
        return None
    return raw_or_none(elem.get_text())


BLOCK_TAGS = {
    "p", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "table",
    "section", "article", "header", "footer", "blockquote", "pre", "dl", "dt", "dd",
}


def rendered_text(node, skip=None) -> str:
    """Văn bản của node như trình duyệt hiển thị: giữ nguyên chữ và khoảng trắng nguồn,
    chỉ thêm xuống dòng ở ranh giới thẻ khối và <br> (để "<li>BI</li><li>SQL</li>"
    không thành "BISQL"). Bỏ qua script/style/comment và node `skip`."""
    out: list[str] = []

    def newline():
        if out and not out[-1].endswith("\n"):
            out.append("\n")

    def walk(el):
        for child in el.children:
            if child is skip:
                continue
            if isinstance(child, Comment):
                continue
            if isinstance(child, NavigableString):
                out.append(str(child))
            elif isinstance(child, Tag):
                if child.name in ("script", "style"):
                    continue
                if child.name == "br":
                    out.append("\n")
                    continue
                block = child.name in BLOCK_TAGS
                if block:
                    newline()
                walk(child)
                if block:
                    newline()

    walk(node)
    return "".join(out)


def section_raw_text(container: Tag, heading: Tag) -> Optional[str]:
    """Text of a section container, excluding the heading element itself."""
    return raw_or_none(rendered_text(container, skip=heading))


def is_working_model_or_metadata(text: str) -> bool:
    """Check if the text is a working model, posting date, or location."""
    normalized = text.strip().lower()
    if normalized in WORKING_MODEL_KEYWORDS:
        return True
    for kw in WORKING_MODEL_KEYWORDS:
        if normalized == kw or normalized.startswith(f"{kw} ") or normalized.endswith(f" {kw}"):
            return True
    for pattern in DISCARD_PATTERNS:
        if pattern.search(normalized):
            return True
    return False


def is_valid_experience_string(text: str) -> bool:
    """Validate whether text qualifies as an actual experience requirement."""
    if is_working_model_or_metadata(text):
        return False
    normalized = text.strip().lower()
    for pattern in EXPERIENCE_PATTERNS:
        if pattern.search(normalized):
            return True
    return False


def extract_raw_job_title(
    soup: BeautifulSoup,
    json_ld_data: Dict[str, Any],
    fallback_title: Optional[str] = None
) -> Optional[str]:
    """
    Extract exact raw job title as displayed on page.
    Preserves parentheses, punctuation, and symbols.
    Never strips parentheses or merges disparate header elements.
    """
    # 1. Primary: exact <h1> element text displayed on the page
    h1_text = element_raw_text(soup.select_one("h1"))
    if h1_text:
        return h1_text

    # 2. Secondary fallback: job-details title heading
    title_text = element_raw_text(soup.select_one(".job-details__title, h3.job-details__title"))
    if title_text:
        return title_text

    # 3. Listing card title fallback
    fb_text = raw_or_none(fallback_title)
    if fb_text:
        return fb_text

    # 4. JSON-LD title as final fallback
    return raw_or_none(json_ld_data.get("title"))


def extract_raw_experience(
    soup: BeautifulSoup,
    json_ld_data: Dict[str, Any]
) -> Optional[str]:
    """
    Extract genuine experience requirement string (e.g. '3+ years of experience', 'Senior').
    Under NO circumstances stores working models ('At office', 'Hybrid', 'Remote')
    or location/posting date strings.
    Assigns None (null in JSON) if no explicit experience metadata string is found.
    """
    candidate_selectors = [
        ".job-experience",
        "[data-testid='experience']",
        ".experience-tag",
        ".job-overview-item",
        ".job-details__overview-item",
        ".preview-header-item",
        ".itag",
    ]

    # 1. Check candidate HTML tags
    for selector in candidate_selectors:
        for elem in soup.select(selector):
            raw_text = element_raw_text(elem)
            check_text = clean_text(raw_text)
            if not check_text:
                continue
            # Strictly reject working models, locations, and timestamps
            if is_working_model_or_metadata(check_text):
                continue
            # Accept if matches actual experience pattern; store the source text unchanged
            if is_valid_experience_string(check_text):
                return raw_text

    # 2. Check JSON-LD experienceRequirements if it's a string
    json_exp = json_ld_data.get("experienceRequirements")
    if isinstance(json_exp, str):
        check_exp = clean_text(json_exp)
        if check_exp and is_valid_experience_string(check_exp):
            return raw_or_none(json_exp)

    return None


def extract_company(soup: BeautifulSoup, json_ld_data: Dict[str, Any]) -> Optional[str]:
    """Extract hiring company name."""
    org = json_ld_data.get("hiringOrganization")
    if isinstance(org, dict) and org.get("name"):
        return raw_or_none(org.get("name"))
    return element_raw_text(soup.select_one(".employer-name, .job-details__sub-title, .job-header-info a"))


def extract_location(soup: BeautifulSoup, json_ld_data: Dict[str, Any]) -> Optional[str]:
    """Extract raw location."""
    job_loc = json_ld_data.get("jobLocation")
    loc_list = []
    if isinstance(job_loc, list):
        for loc in job_loc:
            if isinstance(loc, dict):
                addr = loc.get("address", {})
                if isinstance(addr, dict) and addr.get("addressLocality"):
                    loc_list.append(str(addr.get("addressLocality")))
    elif isinstance(job_loc, dict):
        addr = job_loc.get("address", {})
        if isinstance(addr, dict) and addr.get("addressLocality"):
            loc_list.append(str(addr.get("addressLocality")))
    if loc_list:
        # Multiple JSON-LD localities are joined as listed by the source.
        return raw_or_none(", ".join(loc_list))

    return element_raw_text(
        soup.select_one(".job-header-info .location, [title='Ha Noi'], [title='Ho Chi Minh']")
    )


def extract_posted_date(json_ld_data: Dict[str, Any]) -> Optional[str]:
    """Extract posted date formatted as YYYY-MM-DD."""
    posted = json_ld_data.get("datePosted")
    if posted and isinstance(posted, str) and len(posted) >= 10:
        return posted[:10]
    return None


DESCRIPTION_HEADINGS = ("job description", "mô tả công việc")
REQUIREMENT_HEADINGS = ("your skills and experience", "yêu cầu", "skills and experience", "kỹ năng")


def extract_descriptions(
    soup: BeautifulSoup,
    json_ld_data: Dict[str, Any]
) -> Tuple[Optional[str], Optional[str]]:
    """Extract job_description and job_requirements as raw section text (heading excluded)."""
    job_description = None
    job_requirements = None

    for h2 in soup.find_all("h2"):
        h2_text = h2.get_text(strip=True).lower()
        parent = h2.find_parent("div")
        if parent is None:
            continue
        if job_description is None and any(kw in h2_text for kw in DESCRIPTION_HEADINGS):
            job_description = section_raw_text(parent, h2)
        elif job_requirements is None and any(kw in h2_text for kw in REQUIREMENT_HEADINGS):
            job_requirements = section_raw_text(parent, h2)

    if not job_description and json_ld_data.get("description"):
        desc_soup = BeautifulSoup(str(json_ld_data.get("description")), "html.parser")
        job_description = raw_or_none(rendered_text(desc_soup))

    return job_description, job_requirements


def parse_job_html(
    html: str,
    url: str,
    crawl_timestamp: str,
    parser_version: str,
    source_job_id: Optional[str] = None,
    fallback_title: Optional[str] = None,
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Parse detail page HTML into a validated record in the 22-field schema.

    Returns:
        (is_valid, record_dict, error_message)
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1. Parse JSON-LD script if available
    json_ld_data: Dict[str, Any] = {}
    for script in soup.find_all("script", type="application/ld+json"):
        if script.string:
            try:
                parsed = json.loads(script.string)
                if isinstance(parsed, dict) and parsed.get("@type") == "JobPosting":
                    json_ld_data = parsed
                    break
            except Exception:
                continue

    # 2. Derive deterministic job_id (SHA256 hex[:16])
    job_id = hashlib.sha256(url.encode()).hexdigest()[:16]

    # 3. Resolve source_job_id
    if not source_job_id and isinstance(json_ld_data.get("identifier"), dict):
        source_job_id = str(json_ld_data.get("identifier", {}).get("value", "")) or None

    # 4. Extract fields
    raw_job_title = extract_raw_job_title(soup, json_ld_data, fallback_title)
    company = extract_company(soup, json_ld_data)
    raw_location = extract_location(soup, json_ld_data)
    posted_date = extract_posted_date(json_ld_data)
    raw_experience = extract_raw_experience(soup, json_ld_data)
    job_description, job_requirements = extract_descriptions(soup, json_ld_data)

    # 5. Schema Validation Rules (§4 & §14):
    # Must have raw_job_title and at least one of job_description or job_requirements
    if not raw_job_title:
        return False, None, "Missing mandatory field: raw_job_title"
    if not job_description and not job_requirements:
        return False, None, "Missing both job_description and job_requirements"

    # 6. Construct the 22-field record (docs/data_schema.md §4)
    record = {
        "job_id": job_id,
        "source": "ITviec",
        "source_job_id": source_job_id if source_job_id else None,
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
