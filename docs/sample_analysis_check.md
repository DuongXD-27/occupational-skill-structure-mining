# SAMPLE ANALYSIS CHECK

**Owner:** Hồ Nhật Triều (20236003)

**Version:** v0.1

**Date:** 2026-09-15

**Question this report answers:** does the sample carry the fields `analysis_spec_v0.1.md` requires, in the right format?

**Sample:** 29 postings — ITviec 21, TopCV 8\. Crawl window 2026-09-15.

**Files:** `data/sample/collection_template.csv`, `data/sample/sample_jobs.jsonl`, `reports/data_quality/sample_data_profile.csv`, `reports/analysis/sample_check_numbers.json`

---

---

# 0\. COLLECTION METHOD

Not the crawler. Postings were read from each rendered page and transcribed.

- 26 of 29 verbatim — original language, original bullets  
- 3 (`sample_010`, `012`, `013`) have a verbatim description but a paraphrased requirements section  
- Each posting is marked in the `note` column

Đạt's crawler output remains the authoritative sample. This one unblocks the schema and format checks only.

---

---

# 1\. MAIN FINDING — ITVIEC EXPOSES TWO STRUCTURED FIELDS

Every ITviec posting carries, above the description:

Skills: Machine Learning; ETL; Big Data; AI; MLOps

Job Expertise: AI / Machine Learning Engineer

Captured as `site_skill_tags` and `site_job_expertise`. All 21 ITviec postings have them. TopCV has no equivalent.

## Three uses

**1\. Partial ground truth for skill extraction.** Not a substitute for the hand-annotated test set that scope section 11 requires, but a second reference at zero labelling cost.

**2\. Third-party title normalization.** `site_job_expertise` collapses 21 raw titles into 8 categories — a benchmark for our own normalization, and a second label set for the RQ4 comparison.

| Category | Count |
| :---- | :---- |
| AI / Machine Learning Engineer | 8 |
| Data Engineer | 5 |
| Data Analyst | 2 |
| Data Scientist | 2 |
| Analytics Engineer | 1 |
| Data Architect | 1 |
| Backend Developer | 1 |
| Automation Tester | 1 |

**3\. First-pass relevance filter.** Both deliberate edge cases fail the site's own classification: `sample_012` → `Backend Developer`, `sample_020` → `Automation Tester`. Useful evidence, but not a replacement for our criteria — the field is assigned by rules we cannot inspect.

## Action

These fields sit in the page header. A crawler targeting only title/description/requirements will miss them. Add both to `data_schema_v1.md` as optional fields.

---

---

# 2\. FIELDS THAT ARE SUFFICIENT

| Field | Result |
| :---- | :---- |
| `job_id` | 29/29 unique |
| `raw_job_title` | 100% populated, 27 distinct values |
| `description` | 100% populated, median 716 chars, bullets preserved in all 29 |
| `requirements` | 29/29 populated |
| `source_url` | 100% valid absolute URLs |
| `crawl_date` | 100% in `YYYY-MM-DD`, single-day window |
| `company` | 100% populated, 27 distinct, none over the 3-posting cap |

Source split: ITviec 72.4%, TopCV 27.6% — under the 80% limit in `analysis_spec_v0.1.md` section 9\.

---

---

# 3\. FIELDS MISSING OR INCOMPLETE

## `skills_extracted` — empty for all 29

The extractor and taxonomy v0.1 are not finished.

**Impact:** RQ2, RQ3 and RQ4 all depend on this field. Until it is populated, only the input contract can be checked — not extraction coverage or median skills per posting, which gate every RQ3 result.

---

## `normalized_job_title` — empty for all 29

Normalization rules belong to the cleaning stage and do not exist yet.

**Estimate only:** a crude rule (strip brackets and seniority words) reduces 27 raw titles to 18, compression 0.667.

---

## `requirements` — 3 postings partially paraphrased

`sample_010`, `012`, `013`. Do not use these to evaluate extraction.

---

## `experience_text` — NA in 4 postings

Feeds no core metric. Record in `data_schema_v1.md` that it is optional.

---

---

# 4\. FORMAT PROBLEMS

## `location` — unusable as collected

**26 distinct strings across 29 postings.** Both sources put a full street address here, not a city:

- `Tòa nhà 319 BQP, số 63 Lê Văn Lương, phường Yên Hòa, Ha Noi`  
- `SSI Tower, 1 Châu Văn Liêm, Tu Liem, Ha Noi`

12 of them refer to Hà Nội.

**Impact:** RQ1's location breakdown would produce 26 groups of size 1\. Largest format problem in the sample.

---

## `description` — 1 posting under 300 characters

`sample_017` at 244 chars, against a median of 716\. Its *requirements* section is long, so description length alone is the wrong test — apply the rule to both fields combined.

---

## Mixed language in one field

`sample_025` alternates Vietnamese and English line by line. `sample_008` is Vietnamese prose with English skill names inline.

**Impact:** the skill dictionary must match inside Vietnamese sentences, not only English ones.

---

## Job codes in descriptions

Both MB Bank postings open with an internal code (`2026TD450985 - Kỹ sư Dữ liệu - Data Engineer`). Low impact, but the extractor will see that line.

---

---

# 5\. FOR THE COLLECTION STAGE — ĐẠT

1. **Capture `Skills` and `Job Expertise` from ITviec.** Page header; a description-only crawler misses them. Highest-value item here.  
2. **Capture city, not street address.** 26 distinct values is useless to RQ1.  
3. **Preserve line breaks.** Verify on the first 10 postings before scaling.  
4. **Apply the text-length rule to description \+ requirements combined.** See `sample_017`.  
5. **Expect heavy irrelevance.** ITviec `data-analysis`: \~4 of the first 20 postings were Data/AI. TopCV `machine-learning-engineer` returned domestic helpers and English teachers. The relevance filter will determine corpus quality more than the crawler will.  
6. **Verify ToS and robots.txt** before scaling, per scope section 8\. Still outstanding.

---

---

# 6\. FOR THE CLEANING STAGE — ĐỨC

1. **Location normalization.** Parse province from a full street address, then map to a closed set plus `Remote` / `Unknown`.  
2. **Seniority decision needed before rules are fixed.** 10 of 29 titles carry a seniority word. Stripping it is what lets `data engineer` reach 9 postings. **Without stripping, no title in the sample reaches 5 — RQ3 has no input at all.** Needs Dương's decision.  
3. **Do not overwrite `raw_job_title`.** Scope section 10\.  
4. **Titles carry non-title content.** `Data Engineer (Có Xe Đưa Đón)` (a benefit), `Head Of Data Tại UpBase-AI & Big Data Ecom Partner` (a slogan), `Data Engineer/Data Analyst level Fresher/Junior/Senior` (two jobs in one posting). The last has no clean answer — recommend flagging and excluding from RQ3, with the rule written down.  
5. **Empty skill list must be `[]`, never null.** Null means "did not run".

---

---

# 7\. EDGE CASES — 13 POSTINGS

Marked `EDGE CASE` in the `note` column.

**Need Dương's decision — include or exclude:**

| ID | Title | Issue |
| :---- | :---- | :---- |
| `sample_012` | Senior Backend Engineer (ML required) | Backend role requiring PyTorch, MLOps, LLM, CV. Site says `Backend Developer` |
| `sample_020` | QA Automation Engineer (MLOps/AI) | QA role measuring mAP, Precision, Recall, IoU. Site says `Automation Tester` |
| `sample_015` | AI Lead \- GenAI, RAG, AI Agents | AI title, generic software-leadership requirements |
| `sample_001` | Data Analyst | Mostly finance/accounting; includes an age and gender restriction |

**Test title normalization:** `sample_018` and `sample_022` (Vietnamese titles), `sample_026` (slogan), `sample_028` (benefit), `sample_029` (two jobs in one posting).

**Test text handling:** `sample_007`, `009`, `017` (short), `sample_025` (mixed language), `sample_020` (benefits next to requirements).

---

---

# 8\. CONCLUSION

**Verdict: sufficient to proceed, with conditions.** The format produces the required fields, and the problems found are fixable before the full crawl. The check is half complete because no extractor exists.

## Confirmed

- 7 required fields populated and correctly formatted  
- 29 postings → 27 distinct raw titles, estimated to compress to 18  
- One title group (`data engineer`, 9\) clears the 5-posting threshold, so the RQ3 input contract is satisfiable  
- No duplicates, no company over the cap, source balance within limits  
- ITviec exposes site skill tags and a normalized role category

## Not confirmed

- **Extraction quality** — no extractor exists. Coverage and median skills per posting are untested, and they gate every RQ3 result.  
- **Title normalization** — no rule set. The compression ratio is an estimate.  
- **Any market finding** — at 29 postings, `analysis_spec_v0.1.md` section 8 defers concentration, entropy, skill pairs, both RQ3 directions, and all of RQ4.

## Blocking

1. Extractor output on this sample  
2. Seniority decision from Dương — the difference between one usable title group and none  
3. Location capture or parsing  
4. Schema decision on `site_skill_tags` and `site_job_expertise` — capture now or lose them  
5. Answers on the four inclusion cases in section 7

## Next step

Re-run this check on Đạt's crawler output with `skills_extracted` populated. The format problems in sections 4 and 5 are cheap now and expensive across 2,000 postings.

---

---

# 9\. REPRODUCE

python scripts/csv\_to\_jsonl.py   \--in data/sample/collection\_template.csv \--out data/sample/sample\_jobs.jsonl

python scripts/profile\_sample.py \--in data/sample/collection\_template.csv

Regenerates `sample_data_profile.csv` and `sample_check_numbers.json`, so this report can be refreshed rather than rewritten.

---

---

# 10\. CHANGELOG

**v0.1** — 2026-09-15 — First version. 29 postings, 26 verbatim, no skill extraction available.

&nbsp;