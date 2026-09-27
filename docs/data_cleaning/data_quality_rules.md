# Data Quality Rules v0.1

## 1. Raw Data Immutability Principle & Standard Field Structure

### 1.1 Raw Data Immutability Principle

1. **Raw Data is Immutable:** All fields ingested from the scraper (`Stage A - Raw fields` such as `raw_job_title`, `raw_location`, `raw_experience`, `job_description`, `job_requirements`, `source_url`...) must never be modified, trimmed, or overwritten in place within the database or raw storage.
2. **Strict Raw vs. Derived Separation:** All cleaning, normalization, numeric extraction, or formatting operations must output to newly created derived fields (`Stage B - Derived fields`). The original raw data remains completely intact alongside cleaned attributes.
3. **Status Flagging Over Physical Deletion:** Records that contain errors, duplicates, or fall outside the research domain are not physically deleted from the analytical corpus. Instead, their statuses are tagged via dedicated indicator fields (`relevance_flag`, `exclusion_reason`, `duplicate_flag`, `duplicate_group_id`). This preserves auditability, transparency, and research reproducibility.

### 1.2 Compliance with Standard Schema Structure

- **Raw Fields (Stage A):** Collected in original format by the scraper; treated as read-only by the cleaning pipeline.
 **Derived Fields (Stage B) Produced by the Cleaning Pipeline:**
  - `normalized_location` (standardized from `raw_location` via QR-02)
  - `experience_min_years`, `experience_max_years` (parsed from `raw_experience` via QR-03)
  - `normalized_job_title` (surface-cleaned from `raw_job_title` via QR-04)
  - `duplicate_flag`, `duplicate_group_id` (flagged via QR-05)
  - `relevance_flag`, `exclusion_reason` (flagged via QR-06 and QR-01)

> **Note on Proposed `quality_flags` Field [Requires Schema Change Request]:** The `quality_flags` field (intended to store granular internal error flags such as `MISSING_*`, `LOCATION_UNRECOGNIZED`...) is not currently part of `data_schema_v1.md §4`.
> - **Proposal:** Add `quality_flags: list[string]` to schema v1.1.
> - **Fallback Strategy:** If not approved, quality flags will be written to a dedicated log file (`data/logs/quality_flags.jsonl`) rather than injected into the primary dataset schema.

---

## 2. QR-01: Missing Value Handling Rules

### 2.1 Definition of "Missing"

A field is considered missing if its value is `null` or an empty string/whitespace-only after trimming.

> **Schema Note (§2):** If a raw field contains an original placeholder string obtained directly from the source website (e.g., "N/A" or "Negotiable"), this is **not considered missing** in the raw stage — it represents genuine raw content. A field is marked missing only when no data was delivered.

### 2.2 Field-by-Field Handling

| Field (Official Schema Name) | Action When Missing | Error Flag |
|---|---|---|
| `raw_job_title` | **Drop record** — without a job title, the vacancy cannot be analyzed | `MISSING_JOB_TITLE` |
| `job_description` and `job_requirements` **both missing** | Retain record; assign `relevance_flag = false`, `exclusion_reason = "INSUFFICIENT_TEXT"` (Scope §7 criterion 5) | `MISSING_TEXT_FIELDS` |
| `job_description` missing, but `job_requirements` present | Retain; use `job_requirements` for skill extraction | `MISSING_JOB_DESCRIPTION` |
| `job_requirements` missing, but `job_description` present | Retain; use `job_description` for skill extraction | `MISSING_JOB_REQUIREMENTS` |
| `source` | **Drop record** — data provenance cannot be established | `MISSING_SOURCE` |
| `source_url` | **Drop record** — cannot perform deduplication or verify provenance | `MISSING_SOURCE_URL` |
| `crawl_timestamp` | Retain, record flag; **do not inject placeholders** | `MISSING_CRAWL_TIMESTAMP` |
| `company` | Retain, record flag; **do not inject placeholders** | `MISSING_COMPANY` |
| `raw_location` | Retain, set `normalized_location = null`; record flag | `MISSING_LOCATION` |
| `raw_experience` | Retain, set `experience_min_years = null`, `experience_max_years = null` | `MISSING_EXPERIENCE` |
| `parser_version` | Retain, record flag | `MISSING_PARSER_VERSION` |

> **Why `raw_job_title`, `source`, and `source_url` are dropped rather than flagged:** These three fields represent **fatal technical defects** (the record cannot be identified, traced, or deduplicated). Scope §7 exclusion criteria are designed to protect records with analytical significance — not technically corrupted records that cannot be referenced.
>
> **Placeholder Rule (Schema §2):** Never populate fields with synthetic values like `"Unknown"`, `"N/A"`, `"none"`, or `"-"`. When data is absent, assign `null`. The only exception is when that literal text was scraped verbatim from the source.

### 2.3 Dataset-Wide Warning Thresholds

- If > 10% of records miss both `job_description` and `job_requirements`: **halt the pipeline and alert the team**.
- If > 20% of records miss `job_requirements` (while having `job_description`): **log warning**, but continue execution.
- If > 30% of records miss `raw_location`: **log warning**, inspect scraper selectors.

### 2.4 Scraping Error Handling (Scope §7 — "Error pages, broken links")

Scraping errors fall under Scope §7 Exclusion Criterion 6 — **must be flagged, not deleted**. The record is preserved for auditing.

> **Execution Precedence between §2.2 and §2.4:** Evaluate §2.2 first (`null` / empty string). Only execute §2.4 when fields **exist and contain content**, but the content is suspiciously brief. A record where both text fields are empty falls under §2.2 (`INSUFFICIENT_TEXT`), never reaching §2.4.
>
> Logic:
> ```python
> if job_description is null/empty and job_requirements is null/empty:
>     → §2.2: INSUFFICIENT_TEXT  # Checked first
> elif len(job_description or "") < 30 and len(job_requirements or "") < 30:
>     → §2.4: SCRAPE_ERROR      # Checked only when text exists but is truncated
> ```

| Scenario | Condition | Action | Error Flag | `relevance_flag` | `exclusion_reason` |
|---|---|---|---|---|---|
| Both text fields empty/null | Handled in §2.2, ignored here | — | — | — | — |
| Both text fields present, but both < 30 characters | Fields have content but are truncated — likely partial scrape failure | Retain, assign flags | `SCRAPE_FAILED` | `false` | `SCRAPE_ERROR` |
| `source_url` cannot be parsed as a valid URL | Invalid URL syntax | **Drop** — cannot trace/audit record | `INVALID_URL` | — | — |
| `raw_job_title` contains HTML tags or error strings ("404", "Page not found") | Title reflects HTTP error | Retain, assign flags | `SCRAPE_ERROR_CONTENT` | `false` | `SCRAPE_ERROR` |

> **Note:** `INVALID_URL` records are dropped because they cannot be audited even if retained. This is a technical failure, not an analytical exclusion.

---

## 3. QR-02: Location Normalization Rules (`raw_location` → `normalized_location`)

> Schema §8: `raw_location` must remain untouched. If normalizable, populate `normalized_location`. All mapping rules must be documented in a dedicated lookup table.

### 3.1 Observed Variations

The `raw_location` field exhibits substantial formatting heterogeneity:
- `"Hà Nội"`, `"Ha Noi"`, `"HN"`, `"Hanoi"`, `"TP. Hà Nội"`
- `"Hồ Chí Minh"`, `"HCM"`, `"HCMC"`, `"TP HCM"`, `"TP.HCM"`, `"Ho Chi Minh City"`
- `"Remote"`, `"Work from home"`, `"WFH"`, `"Làm việc từ xa"`
- `"Toàn quốc"`, `"Nationwide"`, `"Cả nước"`
- Multi-location: `"Hà Nội, Hồ Chí Minh"`, `"HN/HCM"`
- District-only names: `"Quận 7"`, `"Quận 1"`, `"Cầu Giấy"`, `"Thanh Xuân"`
- Placeholder strings: `"Not Available"`, `"Not Available, Not Available"`

### 3.2 Standardization Mapping (`location_mapping`)

Summary of primary patterns:

| Pattern (Regex, Case-Insensitive) on `raw_location` | `normalized_location` Value |
|---|---|
| `ha.?noi\|hà.?nội\|\bhn\b` | `Hà Nội` |
| `ho.?chi.?minh\|hồ.?chí.?minh\|\bhcm\b\|hcmc\|tp\.?\s*hcm\|sài.?gòn\|sai.?gon` | `Hồ Chí Minh` |
| `da.?nang\|đà.?nẵng\|\bdn\b` | `Đà Nẵng` |
| `can.?tho\|cần.?thơ` | `Cần Thơ` |
| `hai.?phong\|hải.?phòng` | `Hải Phòng` |
| `binh.?duong\|bình.?dương` | `Bình Dương` |
| `dong.?nai\|đồng.?nai` | `Đồng Nai` |
| District names in HCMC (`quận\s*1\b`, `quận\s*7\b`, `tân\s*bình`, `thủ\s*đức`...) | `Hồ Chí Minh` |
| District names in Hanoi (`cầu\s*giấy`, `thanh\s*xuân`, `đống\s*đa`, `ba\s*đình`...) | `Hà Nội` |
| `remote\|wfh\|work.?from.?home\|làm.?việc.?từ.?xa\|online` | `Remote` |
| `toàn.?quốc\|nationwide\|cả.?nước` | `Toàn quốc` |
| Multiple provinces/cities (comma or `/` across regions) | `Nhiều địa điểm` |
| Placeholder string (`not available`, `n/a`, `unknown`) | `null` + flag `MISSING_LOCATION` |
| Unrecognized pattern | `null` + flag `LOCATION_UNRECOGNIZED` |

### 3.3 Application Rules

1. Input: `raw_location` — immutable, never modified in place.
2. Trim leading/trailing whitespace before matching.
3. If `raw_location` contains both Hanoi and Ho Chi Minh City → `normalized_location = "Nhiều địa điểm"`.
4. If `raw_location` contains a recognized district name → map to the corresponding province/municipality.
5. If `raw_location` matches a placeholder (e.g. `'Not Available'`) → `normalized_location = null`, flag `MISSING_LOCATION`.
6. If no pattern matches → `normalized_location = null`, flag `LOCATION_UNRECOGNIZED`.
7. **Do not write synthetic placeholders** like `"Unknown"` into `normalized_location`.

---

## 4. QR-03: Experience Normalization Rules (`raw_experience` → `experience_min_years` / `experience_max_years`)

> Schema §9: `raw_experience` preserves the original raw text. `experience_min_years` and `experience_max_years` are derived numerical fields. If the number of years cannot be reliably extracted, assign `null`. **Never make ungrounded assumptions or arbitrary estimations.**

### 4.1 Observed Variations

The `raw_experience` field exhibits diverse expressions:
- Range: `"1-3 năm"`, `"1 - 3 years"`, `"từ 1 đến 3 năm"`
- Lower bound only: `"Trên 2 năm"`, `"Over 2 years"`, `"2+ years"`, `">2 năm"`
- Upper bound only: `"Dưới 1 năm"`, `"< 1 year"`, `"Fresher"`
- Open / Non-specific: `"Không yêu cầu"`, `"All levels"`, `"Any"`, `"N/A"`
- Single integer: `"3 năm"` (min and max assumed identical)
- Seniority levels without numbers: `"Senior"`, `"Junior"`, `"Mid-level"`
- Scraper anomalies: Working mode or office addresses accidentally captured (e.g., `"At office"`, `"Hybrid"`, `"174 Thai Ha"`).

### 4.2 Parsing Rules → `experience_min_years` / `experience_max_years`

> **Distinguishing Special Values — incorrect usage skews statistical distributions:**
> - `null` = **Indeterminate / Unknown** (no data or parsing failure)
> - `-1` in `experience_max_years` = **Explicitly unbounded above** (e.g., "2+ years")
>
> When computing experience statistics: filter `IS NOT NULL` first, then separate `experience_max_years != -1` for upper bound calculations.

| Pattern in `raw_experience` | `experience_min_years` | `experience_max_years` | Notes |
|---|---|---|---|
| `"X-Y năm/years"` | X | Y | Concrete range |
| `"Trên X"`, `"X+"`, `">X"`, `"≥X"` | X | -1 | Minimum X known, upper bound unbounded |
| `"Dưới X"`, `"<X"`, `"≤X"` | 0 | X | Maximum X known |
| `"X năm/years"` (single number) | X | X | Presumed min = max |
| `"Fresher"`, `"0 năm"`, `"Không yêu cầu"` | 0 | 0 | Entry level |
| `"Any"`, `"All levels"`, missing/null | null | null | Indeterminate |
| `"Senior"`, `"Junior"`, `"Mid-level"` | null | null | Note: Do not convert seniority levels to numbers. Flag `EXPERIENCE_LEVEL_ONLY`. Schema §9 prohibits estimation. |
| Working mode string (`"At office"`, `"Hybrid"`...) | null | null | Scraper field mismatch. Flag `MISSING_EXPERIENCE` and notify scraper maintainer. |

### 4.3 Application Rules

1. Input: `raw_experience` — immutable, never modified in place.
2. Normalize text for regex matching: lowercase, strip Vietnamese accents.
3. Priority: parse bounded ranges (X-Y) first, followed by one-sided inequalities (X+, <X), and finally single numbers.
4. If unparseable → `experience_min_years = null`, `experience_max_years = null`, flag `EXPERIENCE_PARSE_FAILED`.
5. If seniority level only → `null`/`null` + flag `EXPERIENCE_LEVEL_ONLY`.

---

## 5. QR-04: Job Title Normalization Rules (`raw_job_title` → `normalized_job_title`)

> Schema §7: `raw_job_title` must preserve original text. `normalized_job_title` is used strictly to eliminate surface and formatting noise — **never** automatically merge distinct roles (e.g., AI Engineer, Machine Learning Engineer, Data Scientist) into a single generic bucket. Semantic grouping belongs to the research analysis phase, not cleaning.

### 5.1 Objectives & Scope Boundaries

Generate `normalized_job_title` as a **pure text cleaning** version of `raw_job_title` — stripping formatting noise — for downstream analytical models. QR-04 **does not map titles to a predefined occupational taxonomy**. Grouping titles into occupational clusters is the core empirical research objective of RQ1 and RQ4.

### 5.2 Basic Text Cleaning Steps

```
Input:  raw_job_title  (immutable)
Output: normalized_job_title (cleaned text, preserving original semantics, NO category replacement)

1. Trim leading and trailing whitespace
2. Normalize internal whitespace (collapse multiple spaces to a single space)
3. Strip meaningless special characters: (), [], leading list numbers, asterisks (*), hashtags (#)
   - Retain: /, +, - when forming technical tokens (e.g., "C++", "R/Python")
4. Title Case: capitalize the first letter of each word
5. Standardize formatting abbreviations (without semantic distortion):
   - "Sr." → "Senior"
   - "Jr." → "Junior"
   - "Mgr." → "Manager"
   - "Eng." → "Engineer"
   - "Dev." → "Developer"
6. Strip extraneous non-title noise: salary mentions ("Up to 75M"), bonuses ("- BONUS"), trailing dangling punctuation ("/")
```

### 5.3 Additional Rules

- If the title explicitly contains two distinct roles (e.g., `Data Engineer / Data Analyst`): preserve both, flag `AMBIGUOUS_TITLE` for analytical handling.
- If title is excessively short (< 3 characters after cleaning): flag `TITLE_TOO_SHORT`.
- If title is excessively long (> 100 characters): truncate at 100 characters, flag `TITLE_TOO_LONG`.
- Never delete the original `raw_job_title`.

> **Note for the Analysis Team:** Mapping `normalized_job_title` to occupational categories is executed entirely within the analysis phase based on empirical clustering — not hard-coded in the cleaning pipeline.

---

## 6. QR-05: Duplicate Detection Criteria

> Schema §12: Never delete duplicate records. Use `duplicate_flag` and `duplicate_group_id` for identification.

### 6.1 Duplicate Definitions

**Exact Duplicate:** Two records sharing the identical `source_url`. The record with the later `crawl_timestamp` is flagged with `duplicate_flag = true`.

**Near Duplicate:** Two records having different `source_url` values but satisfying ALL of the following criteria:
- Identical `company` (after whitespace trim and lowercase)
- `normalized_job_title` token overlap ≥ 60% (Jaccard on word tokens) — allows Senior/Non-Senior variants of the same role to be caught
- Identical `normalized_location`
- `job_description` cosine similarity ≥ 0.80 (computed on bag-of-words or TF-IDF representations) — **this is the primary gate**

> **Rationale for relaxed title constraint:** Requiring *identical* titles caused the MB Bank pair (#36 Senior Data Engineer vs #40 Data Engineer) to escape detection despite 88% JD similarity. The `job_description` similarity threshold is the authoritative signal; the title overlap acts as a secondary guard against false positives.
>
> If similarity calculation tools are not yet loaded: apply the initial heuristic — compare the first 200 characters of `job_description` after lowercasing and stripping whitespace. Two records with identical first-200-char prefixes under the same company are treated as near-duplicates.
>
> **False Positive Guard:** Records with different seniority levels (Senior vs Non-Senior) that meet the JD threshold are flagged `DUPLICATE_NEAR` but also receive flag `SENIORITY_VARIANT` in `quality_flags`. Analysts may choose to retain both for longitudinal seniority research.

### 6.2 Processing

1. **Do not delete** duplicate records from the raw dataset.
2. Assign `duplicate_flag = true` to secondary duplicate records.
3. Assign `duplicate_group_id` equal to the `job_id` of the canonical representative record (the earliest collected record).
4. Append `DUPLICATE_EXACT` or `DUPLICATE_NEAR` to `quality_flags`.
5. The default analytical corpus retains only one canonical record per duplicate group (Schema §12).

### 6.3 Warning Thresholds

- If proportion of `duplicate_flag = true` > 15%: **issue warning**, inspect scraper for redundant crawl paths.

---

## 7. QR-06: Criteria for Identifying Non-Data/AI Postings

> Schema §11: Use `relevance_flag` (boolean). When `relevance_flag = false`, `exclusion_reason` is **mandatory** and must use standardized labels from a predefined taxonomy — no arbitrary free-text allowed.

### 7.1 Objectives

Flag (without deleting) job postings outside the Data/AI domain to exclude them from the primary analytical corpus.

QR-06 directly implements the **Inclusion Criteria (§6)** and **Exclusion Criteria (§7)** defined in `project_scope_v1.md`.

> **Note on Market Scope (Scope §5):** The domain list in §5 (Data Analysis, ML, NLP...) represents search boundaries for the *scraper* — **not an occupational taxonomy**. QR-06 must not use this list to hard-label vacancies. Domain classification is the research outcome of RQ1/RQ4.

### 7.2 Step 1 — Exclusion List Pre-Check (Title Gate)

**Run this step FIRST, before the Whitelist Check.** Inspect `normalized_job_title` against the exclusion patterns defined in §7.3.

- If the title matches a standard exclusion group → `relevance_flag = false`, `exclusion_reason = "NOT_DATA_AI_ROLE"`. **Stop — do not run the Whitelist Check.**
- If the title matches the Data Entry pattern → `relevance_flag = false`, `exclusion_reason = "DATA_ENTRY_ROLE"`. **Stop.**

> **Rationale:** Running the Whitelist Check before the Exclusion Check caused false positives: roles like "Advertising Monetization Specialist" (excluded by title under the Sales/Marketing group) were incorrectly retained because `job_requirements` contained technical keywords such as `SQL` or `API`. The title is the most reliable primary signal for domain scope. Whitelist scanning of `job_description`/`job_requirements` must only execute after the title is confirmed to not belong to an excluded category.

### 7.3 Step 2 — Whitelist Core Data/AI Keyword Check

Execute only if the record was **not** excluded in Step 1. Check `raw_job_title` first, then `job_description` and `job_requirements`. If any field contains at least one of the following core keywords → set `relevance_flag = true` and terminate check:

```
python, r language, sql, spark, hadoop, kafka, airflow, dbt,
pandas, numpy, scikit-learn, tensorflow, pytorch, keras,
machine learning, deep learning, neural network, nlp, llm, gpt,
computer vision, data pipeline, etl, elt, data warehouse, data lake,
power bi, tableau, looker, metabase, superset,
data analyst, data engineer, data scientist, data architect,
bi analyst, analytics engineer, mlops, llmops,
vector database, embedding, rag, fine-tuning,
statistics, regression, classification, clustering, recommendation system
```

> Cross-reference this list with Cường's `taxonomy/skills_taxonomy.csv` to ensure alignment between filtering and extraction.

### 7.4 Step 3 — Exclusion List Pattern Reference

This table is used in Step 1 (§7.2). The exclusion list is formulated directly from **Exclusion Criteria §7** of `project_scope_v1.md`:

| Exclusion Category (Source: Scope §7) | Pattern Examples |
|---|---|
| Pure IT — no Data/AI engineering or analytical tasks | `software engineer`, `web developer`, `mobile developer`, `devops engineer`, `system admin`, `network engineer`, `qa engineer`, `tester`, `sap specialist`, `sap mm`, `sap fico` |
| Sales / Marketing for AI or Tech products | `sales`, `marketing`, `business development`, `account manager`, `hr`, `recruiter`, `monetization specialist` |
| Data Entry — clerical input without analytics | `data entry`, `data input`, `nhập liệu` |
| Operations / Finance / Accounting | `accountant`, `finance`, `logistics`, `supply chain`, `operations` |
| UI/UX & Graphic Design | `ui/ux designer`, `graphic designer` |
| General Management / Scholarships (non-technical) | `general manager`, `project manager`, `scholarship` |

> **Internship / Fresher:** Scope §6 explicitly retains interns/freshers if the role is *authentically* technical Data/AI. Do not filter out candidates purely by seniority level — evaluate content.
>
> **Ambiguous Titles:** When a title contains both a Data/AI token *and* an exclusion token (e.g., "AI Sales Manager"), the exclusion pattern takes precedence. The record is flagged `NOT_DATA_AI_ROLE` with a secondary note `AMBIGUOUS_CLASSIFICATION` in `quality_flags` for manual review.

### 7.5 Step 4 — Truncated Text Verification

- If `job_description` < 50 characters after trimming → assign flag `DESCRIPTION_TOO_SHORT`, route to manual review.

### 7.6 Standardized `exclusion_reason` Taxonomy

Schema §11 mandates standardized labels. The vocabulary is derived from Scope §7 Exclusion Criteria:

| Label | Definition | Scope §7 Source | Assigned By |
|---|---|---|---|
| `NOT_DATA_AI_ROLE` | Title confirms role is outside Data/AI scope (exclusion list match) | §7 criteria 1, 3, 4 | QR-06 Step 1 |
| `DATA_ENTRY_ROLE` | Pure data entry role — lacks analytical or engineering tasks | §7 criterion 2 | QR-06 Step 1 |
| `INSUFFICIENT_TEXT` | Both text fields missing — insufficient data to evaluate relevance | §7 criterion 5 | QR-01 §2.2 |
| `SCRAPE_ERROR` | Error page, broken link, or corrupt scraped content | §7 criterion 6 | QR-01 §2.4 |
| `MANUAL_REVIEW_REQUIRED` | Unrecognized role matching neither whitelist nor exclusion list — held for human review | — | QR-06 Step 3 |

### 7.7 Decision Flow Rules

1. **Step 1 — Exclusion Title Gate (§7.2):**
   - If title matches standard exclusion group → `relevance_flag = false`, `exclusion_reason = "NOT_DATA_AI_ROLE"`. **Stop.**
   - If title matches Data Entry pattern → `relevance_flag = false`, `exclusion_reason = "DATA_ENTRY_ROLE"`. **Stop.**
2. **Step 2 — Whitelist Check (§7.3):** If title was not excluded in Step 1 → scan `raw_job_title`, `job_description`, `job_requirements` for whitelist keywords. If any match → `relevance_flag = true`. **Stop.**
3. **[Explicit Default]** If matching neither list → `relevance_flag = true`, append `MANUAL_REVIEW_REQUIRED` to `quality_flags` — default to retaining for human audit.
4. **Step 4 — Text Quality Check (§7.5):** If `job_description` < 50 characters → append flag `DESCRIPTION_TOO_SHORT`; if both text fields < 50 characters → assign `exclusion_reason = "INSUFFICIENT_TEXT"`.
5. Never delete records.
6. The default analysis corpus filters `relevance_flag = true` and `duplicate_flag = false`.

> **Validated against sample data:** Record #11 "Advertising Monetization Specialist" — previously a false positive under the old flow (whitelist ran first, `SQL` in requirements triggered `relevance_flag = true`). Under the corrected flow, Step 1 matches `monetization specialist` in the Sales/Marketing exclusion group and assigns `relevance_flag = false, exclusion_reason = "NOT_DATA_AI_ROLE"` before the whitelist scan is reached.

---


## 8. Notes on Issues Discovered from 30–50 Sample Postings

| No. | Empirically Observed Issue | Impacted Proportion | Affected Fields | Assessment & Rule-Based Handling |
|---|---|---|---|---|
| 1 | **Scraper Experience Field Mismatch:** The crawler mapped working mode and office addresses into `raw_experience` instead of years of experience. Breakdown (substring match): `At office`: 33 records (exact); `Hybrid`: 5 records (3 exact + 2 composite `"Hybrid, [address]"`); `Remote`: 2 records (1 exact + 1 composite `"Remote, Da Nang"`); office addresses only: 5 records (#09, #10, #20, #28, #45). | 45/45 records (100.0%) | `raw_experience` | **Scraper fix requested from Đạt.** QR-03 cannot parse experience numbers from this field until the scraper is patched; experience numbers must temporarily be extracted from `job_requirements`. |
| 2 | **Location Missing Province/City & Placeholder Present:** 20 records contain the string `'Not Available'` at any position (44.4%); 8 records are multi-location strings containing a comma separator (e.g., `'Quận 1, Quận Đống Đa'`, `'Quận Phú Nhuận, Not Available'`); 21 records contain district-only names (`Quận 1`, `Quận 7`, `Thanh Xuân`, `Cầu Giấy`, `Tây Hồ`, `Nam Từ Liêm`, `Thành phố Thủ Đức`...) without city names. Note: some records belong to multiple groups (e.g., multi-region records that also contain 'Not Available'). | 45/45 records (100.0%) | `raw_location` | Apply QR-02: convert `'Not Available'` component to `null` with flag `MISSING_LOCATION`. Map district names to provinces via `location_mapping.csv`. Multi-regional postings mapped to `'Nhiều địa điểm'`. |
| 3 | **Job Title Formatting Noise:** Embedded salaries (`Up to 75M`), bonus perks (`- BONUS`), trailing syntax noise (`English required, /`), typos (`Appllication/Intergration`), and 34/45 titles concatenating tech stack keywords. | 38/45 records (84.4%) | `raw_job_title` | Apply QR-04: perform surface cleaning, strip extraneous salary/perk/punctuation noise, standardize casing into `normalized_job_title`. Original text preserved in `raw_job_title`. |
| 4 | **Out-of-Scope Postings:** 4 records belong to ERP roles (`Senior SAP Specialist`), general scholarships (`VPBank Scholarship`), ad operations (`Ad Monetization Specialist`), and software testing (`Internship BA/QA`). | 4/45 records (8.9%) | `raw_job_title`, `job_description` | Apply QR-06: exclude from main analytical corpus by assigning `relevance_flag = false`, `exclusion_reason = "NOT_DATA_AI_ROLE"`. |
| 5 | **Near-Duplicate Job Postings — Empirically Validated:** Computed via TF-IDF cosine (JD) and Jaccard (title tokens) directly from data. **Confirmed pair:** #36 `"Senior AI Expert Machine Learning, Deep Learning, LLM"` vs #40 `"AI Expert Computer Vision/NLP/LLM"` (both MB Bank) — Title Jaccard = 0.30 (below 60% threshold), JD TF-IDF cosine = 0.988 (well above 80% threshold). **Not caught by QR-05** because the AND-logic requires both conditions to pass — this is a known edge case flagged for Leader review (see note below). **False positive pair:** #27 `"Snr/Lead Data Engineer Pyspark, Snowflake - BONUS"` vs #33 `"Snr/Lead Data Software Engineer Pyspark, Snowflake"` (both EPAM Vietnam) — Title Jaccard = 0.75 (above 60%), JD cosine = 0.51 (below 80% threshold). JD-gate correctly rejects this pair — two genuinely distinct role descriptions under similar titles. | 4/45 records (8.9%) | `company`, `job_description` | **For the confirmed MB Bank pair:** QR-05b AND-logic cannot flag these records under current thresholds (title Jaccard 0.30 < 60%). Recommend Leader discussion to allow JD-cosine alone as a sufficient gate when cosine ≥ 0.95 — this would catch the #36/#40 pair without broadening false-positive risk. **For EPAM pair:** No action needed; JD-gate correctly excluded. |
| 6 | **Missing Salary and Education Fields:** 100% of records lack `salary_raw` and `education` due to ITviec login gating for salaries and absence of a standalone education element on the UI. | 45/45 records (100.0%) | `salary_raw`, `education` | Apply QR-01: assign `null`, avoid synthetic placeholders per Schema §2 and §10 immutability standards. |

> **Note to Leader — QR-05 AND-Logic Limitation:** The MB Bank pair (#36 Senior AI Expert ML/DL/LLM vs #40 AI Expert CV/NLP/LLM) has JD cosine = 0.988 but title Jaccard = 0.30. Under the current AND-logic (title ≥ 60% AND JD ≥ 0.80), this pair is not flagged. These are likely the same job template posted under different specialization headings. Proposed adjustment: introduce a high-confidence JD-only path — if JD cosine ≥ 0.95 AND same company → flag `DUPLICATE_NEAR` + `SENIORITY_VARIANT` regardless of title overlap. This preserves safety for lower-similarity pairs while catching near-identical JD templates.
