# DATA SCHEMA V1

## 1. Purpose

This document defines the unified data structure for the entire project.

All team members must use identical field names and definitions.

Members are not permitted to rename, delete, or alter the semantics of any field without the Leader's explicit approval.

Current version: v1.0

---

## 2. General Conventions

### Field Names

Use `snake_case`.

Examples:

`raw_job_title`
`normalized_job_title`
`crawl_timestamp`

Do not use:

`RawJobTitle`
`raw-job-title`
`Raw Job Title`

### Text

Store in UTF-8 encoding.

Do not remove Vietnamese diacritics from raw data.

### Missing Values

Use `null` for missing data.

Do not arbitrarily use placeholder values such as:

"N/A"
"unknown"
"-"
"none"

unless it represents the literal raw text obtained directly from the source and is stored within a raw field.

### Dates

Use the format:

`YYYY-MM-DD`

### Timestamps

Use ISO 8601 and include time zones whenever available.

### Boolean

Use only:

`true`
`false`

### Currency

If currency information is available, use standard ISO currency codes, such as:

`VND`
`USD`

### Experience

Standardized years of experience fields must use the unit:

years.

### Raw Data

Do not overwrite raw fields with normalized or derived data.

---

## 3. Data Stages

The project comprises four primary data stages:

### Stage A — Raw data

Data directly extracted from sources by the parsers.

### Stage B — Clean data

Data that has been cleaned, normalized, and annotated with relevance and duplicate flags.

### Stage C — Skill features

Data with extracted skills.

### Stage D — Analysis outputs

Derived tables supporting similarity measurement, clustering, and visualization.

---

## 4. Main Vacancy Schema

| Field | Description | Type | Required | Source/Derived | Normalized? |
|---|---|---|---|---|---|
| job_id | Unique internal ID | string | Yes | Derived | No |
| source | Recruitment platform / source | string | Yes | Raw | No |
| source_job_id | Posting ID from website if available | string/null | No | Raw | No |
| source_url | Detail page URL | string | Yes | Raw | No |
| crawl_timestamp | Collection timestamp | datetime | Yes | Raw | No |
| parser_version | Parser version | string | Yes | Raw | No |
| raw_job_title | Original job title | string | Yes | Raw | No |
| normalized_job_title | Surface-normalized job title | string/null | Post-cleaning | Derived | Yes |
| company | Company name | string/null | No | Raw | Limited |
| raw_location | Original location string | string/null | No | Raw | No |
| normalized_location | Normalized location | string/null | No | Derived | Yes |
| posted_date | Posting date if available | date/null | No | Raw/Parsed | Format normalized only |
| raw_experience | Original experience requirement string | string/null | No | Raw | No |
| experience_min_years | Minimum years of experience | number/null | No | Derived | Yes |
| experience_max_years | Maximum years of experience | number/null | No | Derived | Yes |
| education | Education requirement | string/null | No | Raw/Parsed | Limited |
| job_description | Job description text | string/null | Conditional | Raw | No |
| job_requirements | Candidate requirements text | string/null | Conditional | Raw | No |
| job_text | Concatenated text for skill extraction | string/null | Post-preprocessing | Derived | Yes |
| salary_raw | Original salary information string | string/null | No | Raw | No |
| salary_min | Minimum salary if parsable | number/null | No | Derived | Yes |
| salary_max | Maximum salary if parsable | number/null | No | Derived | Yes |
| salary_currency | Currency code | string/null | No | Derived | Yes |
| relevance_flag | Whether posting is within research scope | boolean | Post-cleaning | Derived | No |
| exclusion_reason | Reason for exclusion | string/null | When relevance=false | Derived | No |
| duplicate_flag | Whether record is a duplicate | boolean | Post-cleaning | Derived | No |
| duplicate_group_id | Group ID identifying duplicate vacancies | string/null | No | Derived | No |
| extracted_skills | List of canonical skills | list[string]/null | Post-extraction | Derived | Yes |
| skill_count | Number of extracted skills | integer/null | Post-extraction | Derived | No |

---

## 5. Mandatory Text Requirements

A valid vacancy posting must contain:

`raw_job_title`

and at least one of the two text fields:

`job_description`
`job_requirements`

If both text fields are empty, the record lacks sufficient data for skill extraction and must be considered for exclusion.

---

## 6. Rules for job_id

`job_id` serves as the internal primary key for the project.

`job_id` must be:

- unique;
- stable across pipeline executions;
- independent of row index / line numbers;
- immutable after cleaning.

If the source website provides a `source_job_id`, maintain it separately in `source_job_id`.

Do not use a specific website's `source_job_id` as the global primary key for the entire project.

---

## 7. Rules for Job Titles

### raw_job_title

Must preserve the exact raw content retrieved from the source.

Do not correct spelling or merge occupations within this field.

### normalized_job_title

Used solely to eliminate superficial and formatting discrepancies.

The normalization step must NOT automatically group:

AI Engineer
Machine Learning Engineer
Data Scientist

into a single broad job family.

Semantic grouping does not belong to the cleaning phase.

---

## 8. Rules for Location

Must retain:

`raw_location`

and, if normalizable, append:

`normalized_location`.

Do not overwrite `raw_location`.

All location mapping rules must be documented in a dedicated mapping file.

---

## 9. Rules for Experience

`raw_experience` retains the original website text.

`experience_min_years` and `experience_max_years` are derived numeric fields.

If the number of years cannot be reliably determined, set to `null`.

Do not make arbitrary assumptions or estimates.

---

## 10. Rules for Salary

`salary_raw` is always preserved as-is if provided by the website.

`salary_min` and `salary_max` are only assigned values when they can be unambiguously parsed into numbers.

If the website states:

Negotiable
Thỏa thuận
Competitive

then `salary_min` and `salary_max` must be set to `null`.

Do not attempt to impute or guess salary amounts.

---

## 11. Rules for Relevance

`relevance_flag = true`:

The posting is retained in the research corpus.

`relevance_flag = false`:

The posting is excluded from primary analyses.

When `relevance_flag = false`:

`exclusion_reason` is mandatory.

Exclusion reasons must draw from a standardized, predefined label set rather than arbitrary free-text comments.

---

## 12. Rules for Duplicates

Do not delete duplicate records from the raw dataset.

Flag duplicates using:

`duplicate_flag`

and, where applicable:

`duplicate_group_id`.

The final research corpus will retain only one representative record per unique vacancy after deduplication is finalized.

---

## 13. Rules for extracted_skills

`extracted_skills` contains only canonical skill names defined in the project taxonomy.

Do not allow mixed representations such as:

AWS
Amazon Web Services

if both have been defined as the same canonical skill.

The skill list must reference the active taxonomy version.

---

## 14. Skill Matrix

The skill matrix is stored separately from the primary vacancy table.

Each row corresponds to one `job_id`.

Basic schema:

`job_id`
`skill_001`
`skill_002`
...
`skill_n`

Cell values:

1 = skill present
0 = skill not detected by the extractor

Skill names or identifiers must reference the taxonomy.

---

## 15. Crawl Log Schema

The crawl log file must contain at least the following fields:

| Field | Description | Type | Required |
|---|---|---|---|
| source | Source platform | string | Yes |
| source_url | Accessed URL | string | Yes |
| crawl_timestamp | Access timestamp | datetime | Yes |
| status | Success / failure status | string | Yes |
| http_status | HTTP status code if available | integer/null | No |
| error_type | Error category | string/null | No |
| error_message | Short description | string/null | No |
| parser_version | Parser version | string | Yes |

---

## 16. Standard Data Files Between Modules

### Raw data

`data/raw/jobs_raw.jsonl`

Producer: Data Collection.

Must not be edited directly after writing.

### Clean data

`data/processed/jobs_clean.parquet`

Producer: Data Cleaning.

This is the primary dataset used by all downstream modules.

### Taxonomy

`taxonomy/skills_taxonomy.csv`

Producer: Skill Extraction.

### Job skill data

`data/features/job_skills.parquet`

Mandatory fields:

`job_id`
`extracted_skills`
`skill_count`

### Job skill matrix

`data/features/job_skill_matrix.parquet`

Mandatory fields:

`job_id`
skill columns

---

## 17. Fields That Must Remain Untouched

The following fields must never be overwritten:

`source`
`source_job_id`
`source_url`
`crawl_timestamp`
`raw_job_title`
`raw_location`
`raw_experience`
`job_description`
`job_requirements`
`salary_raw`

If transformations are required, create new derived fields.

---

## 18. Fields Allowed for Normalization

Derived fields that may be normalized:

`normalized_job_title`
`normalized_location`
`experience_min_years`
`experience_max_years`
`salary_min`
`salary_max`
`salary_currency`
`job_text`
`extracted_skills`

All significant normalization rules must have corresponding documentation or mapping files.

---

## 19. Schema Change Protocol

Once Schema v1 is locked by the Leader:

- Do not add fields arbitrarily;
- Do not delete fields arbitrarily;
- Do not rename fields arbitrarily;
- Do not alter data types arbitrarily.

If a schema change is necessary, the member must report:

1. The target field(s);
2. Justification / rationale;
3. Impacted downstream modules;
4. Strategy for handling legacy data.

Leader approval is required before issuing the next schema version.

---

## 20. Versioning Principles

Minor backward-compatible updates:

v1.0 → v1.1

Breaking changes affecting schema structure or dependent modules:

v1.x → v2.0

All datasets used to produce primary research results must explicitly record their schema version.