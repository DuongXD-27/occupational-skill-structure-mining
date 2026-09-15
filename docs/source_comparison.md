# SOURCE COMPARISON

**Owner:** Hồ Nhật Triều (20236003)

**Version:** v0.1

**Date:** 2026-09-15

**Purpose:** compare candidate sources on what they expose, to support the source selection required by `project_scope_v1.md` section 8\.

**Method:** listing pages and a sample of detail pages read from the rendered page of each site. Not a full crawl.

---

## Sources surveyed

**Named as candidates in `project_scope_v1.md` section 8:**

- ITviec  
- TopCV  
- CareerViet

**Added by the author of this document, not named in the scope:**

- VietnamWorks

VietnamWorks was surveyed because it is a large Vietnamese job board and its absence from the candidate list appeared to be an oversight rather than a decision. **The survey concludes it should not be used** (section 2.4), so nothing in the scope's candidate list needs to change. It is listed here only so the leader knows where the fourth column came from.

---

## Scope constraint

Section 8 allows a maximum of **two** sources in the corpus — one primary, one backup.

This document does not propose using four. It surveys four so that the choice of two rests on evidence rather than assumption.

---

---

# 1\. FIELD AVAILABILITY

| Field | ITviec | TopCV | CareerViet | VietnamWorks |
| :---- | :---- | :---- | :---- | :---- |
| Job title | yes | yes | yes | yes |
| Company | yes | yes | yes | sometimes anonymous |
| Description | yes | yes | yes | yes |
| Requirements (separate) | yes | yes | yes | yes |
| **Site skill tags** | **yes** | no | **yes** | **yes, low quality** |
| **Normalized role category** | **yes** | no | no | no |
| **Seniority as its own field** | no | no | **yes** | no |
| **Experience as its own field** | no | yes | **yes** | no |
| Salary | hidden behind login | yes | **yes, real ranges** | yes, sometimes USD |
| Industry category | yes | no | **yes** | no |
| Employment type | no | no | **yes** | no |
| Education level | no | no | **yes** | no |
| Benefits list | free text | free text | **structured list** | free text |
| Posting expiry date | no | no | **yes** | no |
| Location granularity | full street address | district \+ address | **province** | province |

---

---

# 2\. SOURCE NOTES

## 2.1 ITviec

**Strongest for:** structured role classification.

Unique advantage: a `Job Expertise` field that assigns each posting a single normalized role category. Across 21 postings it collapsed 21 raw titles into 8 categories. Nothing else surveyed has this. It is a ready-made benchmark for our own title normalization, and a second label set for the RQ4 cluster comparison.

Skill tags are clean, English, 4–6 per posting.

Weaknesses:

- Salary requires login, so that field is unusable.  
- Location is a full street address, not a province — 26 distinct strings across 29 postings in the sample.  
- Seniority appears only inside the title.  
- Keyword listing pages are heavily polluted: of the first 20 postings on `it-jobs/data-analysis`, roughly 4 were technical Data/AI roles. The rest were Business Analyst, UI/UX, Solution Architect and banking roles.

---

## 2.2 TopCV

**Strongest for:** volume.

Exposes experience as its own field and shows salary. Descriptions keep bullet structure.

Weaknesses:

- No skill tags, no role category.  
- **Worst relevance of the four.** The page for `machine-learning-engineer` returned domestic helper roles, English teacher roles, and video editor roles. A keyword crawl here would need very aggressive filtering.  
- Titles frequently carry non-title content: `Data Engineer (Có Xe Đưa Đón)` puts a shuttle-bus benefit in the job title.

---

## 2.3 CareerViet

**Strongest for:** structured metadata.

Richest field set of the four. Two fields matter directly to this project:

- **`Cấp bậc` (level)** — seniority as a separate field, values such as `Nhân viên`, `Trưởng nhóm / Giám sát`. This is the open question in `analysis_spec_v0.1.md` section 9 ⑥, answered at the source instead of parsed out of the title.  
- **`Kinh nghiệm`** — experience as a separate field (`5 - 10 Năm`, `Trên 2 Năm`), not buried in prose.

Also exposes `JOB TAGS / SKILLS`, industry, employment type, education level, age limit, a structured benefits list, posting expiry date, and a real salary range rather than "negotiable".

Weaknesses:

- **Longest and messiest titles of the four.** Example: `Trung tâm Quản trị và phân tích dữ liệu - Trưởng bộ phận Tích hợp dữ liệu (Data Engineer)` — a department name, a role, and an English gloss in one field. Normalization will be hardest here.  
- Descriptions are Vietnamese-dominant, so the skill dictionary must handle Vietnamese well.  
- Relevance is moderate: a plastics-factory `Kỹ Sư Quản Lý Chất Lượng - QA QC Engineer` appeared in a `data engineer` search. Its description is genuinely data-adjacent (MES, ERP, SAP, dashboards, root-cause analysis), which makes it a hard inclusion call rather than an obvious reject.

---

## 2.4 VietnamWorks

**Not a scope candidate.** Surveyed as an extra; see the header.

**Strongest for:** nothing that the others do not do better.

Has skill tags, but low quality — `Sql- Python Or R` appears as a single tag, and casing is inconsistent across Vietnamese and English (`Công Cụ ETL`, `Khoa Học Dữ Liệu`).

Weaknesses that matter for crawler design:

- **Pages are JavaScript-rendered.** A plain HTTP fetch returns "Loading interface…" and no jobs. Requires a headless browser, which raises crawler cost and fragility.  
- **Expired postings soft-404.** A dead posting returns HTTP 200 with a generic "page not found" body and a list of unrelated jobs. A crawler checking only status codes would silently ingest garbage.  
- **Anonymous employers.** Headhunter listings show `Navigos Search's Client` instead of a company name, so the company field is not a real employer.  
- **Near-duplicates within the source.** `[Hà Nội_Banking] Data Analyst_Credit Risk & Portfolio Analytics` and `[Hanoi_Banking] Data Analyst_Credit Risk & Portfolio Analytics` are the same vacancy posted twice with different bracket text.

---

---

# 3\. THE FINDING THAT AFFECTS RQ1 DIRECTLY

## Cross-source duplicates carry different titles

MB Bank's internal job code `2026TD450985` appears on both ITviec and CareerViet. The descriptions are identical. The titles are not:

| Source | Title |
| :---- | :---- |
| ITviec | `Data Engineer - Data Division` |
| CareerViet | `Kỹ sư Dữ liệu - Data Engineer - Khối Dữ liệu (2026TD450985)` |

**One vacancy. Two sources. Two different titles, in two different languages.**

## Why this matters

A duplicate here does not just double-count — **it adds a title**. RQ1's fragmentation metric would then measure syndication, not employer naming behaviour. Scope section 15 lists syndicated vacancies as a known limitation; this is a concrete instance.

## Consequences

- Dedup **cannot** match on title — the titles differ in wording and language.  
- Dedup must work **across sources**, not only within one.  
- Workable key: description similarity, or an employer job code. MB Bank prints its code in the description on both sites.  
- Running primary and backup **in parallel** multiplies the problem. As fallback-only, it mostly disappears. The leader should state which.

---

---

# 4\. WHAT EACH SOURCE WOULD COST US

|  | ITviec | TopCV | CareerViet | VietnamWorks |
| :---- | :---- | :---- | :---- | :---- |
| Crawler complexity | low | low | low | **high (JS \+ soft-404)** |
| Relevance filtering burden | high | **very high** | moderate | high |
| Title normalization burden | moderate | moderate | **high** | moderate |
| Fields we would otherwise have to derive | **fewest** | most | **fewest** | most |
| Vietnamese-language handling required | moderate | high | **high** | high |

---

---

# 5\. RECOMMENDATION

A recommendation to the leader, not a decision.

**Primary: ITviec.** Only source with a normalized role label (`Job Expertise`) — a benchmark for our normalization and a second label set for RQ4. Simplest crawler.

**Backup: CareerViet.** Richest metadata; its separate seniority and experience fields remove two parsing problems. Messiest titles — a cost, though arguably a feature for RQ1.

**Not recommended: VietnamWorks.** JS rendering plus soft-404s make the crawler materially harder for no unique field. It was not a scope candidate, and this survey gives no reason to add it.

**Not recommended as primary: TopCV.** Relevance is too poor; the filter would be doing most of the work and its errors would dominate corpus quality.

**If ITviec and CareerViet are both used, decide whether they run in parallel or as fallback**, per section 3\.

---

---

# 6\. ACTIONS

**For the leader**

1. Choose primary and backup from this evidence.  
2. State whether the backup runs in parallel or only on failure.  
3. Decide whether seniority comes from a source field (`Cấp bậc`, CareerViet only) or from parsing the title.

**For the collection stage**

4. Capture `Skills` and `Job Expertise` from ITviec — they sit in the page header, above the description, and a crawler targeting only title/description/requirements will miss them.  
5. Capture `Cấp bậc` and `Kinh nghiệm` if CareerViet is used.  
6. Record HTTP status **and** detect soft-404 bodies, if VietnamWorks is used at all.  
7. Extract employer job codes from description text where present — they are the most reliable cross-source dedup key found so far.

**For the cleaning stage**

8. Write the dedup rule to work across sources and without relying on title.

---

---

# 7\. LIMITS OF THIS SURVEY

- Based on listing pages and roughly 35 detail pages, not a full crawl.  
- Three of the four sources are the scope candidates; VietnamWorks was added by the author.  
- Relevance rates are from one keyword page per source and are indicative only.  
- No Terms of Service or robots.txt review was performed. `project_scope_v1.md` section 8 requires that before large-scale collection, and it is still outstanding.  
- Field availability was checked on Data/AI postings only. Other categories may differ.

---

---

# 8\. CHANGELOG

**v0.1** — 2026-09-15 — First version.

&nbsp;