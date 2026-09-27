# SAMPLE ANALYSIS CHECK

**Owner:** Hồ Nhật Triều (20236003) · **Version:** v0.2 · **Date:** 2026-09-24

**Dataset:** `data/sample/sample_jobs.jsonl` — 45 postings, ITviec, parser v0.1, posted 2026-08-13 to 2026-09-15

**Question:** can we run the analyses in `analysis_spec_v0.1.md` on this data yet?

---
---

# 1. VERDICT

| Analysis | Can we run it? | Why not |
|---|---|---|
| RQ1 — count the job titles | As a test only | — |
| RQ1 — measure title fragmentation | **No** | Titles are not read correctly |
| RQ1 — break down by location | **No** | 24 of 45 locations unusable |
| RQ2 — which skills are common | **No** | Skills not extracted yet |
| RQ2 — which skills go together | **No** | Same, plus too few postings |
| RQ3 — same title, different skills | **No** | **No title has 5 postings**, and no skills extracted |
| RQ3 — different titles, same skills | **No** | Skills not extracted yet |
| RQ4 — let the algorithm group jobs | **No** | 45 postings, we need 300 |
| RQ4 — PCA chart | **No** | It draws the RQ4 result, which does not exist |

## Three reasons

**One real defect.** Job titles are stored incorrectly. This is ours to fix — see section 2. It is one of the two things blocking RQ3.

**Waiting on the extractor.** Skills have not been extracted, so nothing that needs skills can run — RQ2, and **both halves of RQ3**.

**Waiting on volume.** RQ4 needs roughly 300 postings. We have 45.

Only the first one needs action now.

---
---

# 2. RQ1 — WHAT JOB TITLES EXIST

**Fields needed:** `raw_job_title`, `normalized_job_title`, `location`

## The numbers

| | |
|---|---|
| Postings | 45 |
| Different job titles | **45** |
| Still different after basic tidying | 43 |
| Titles that appear only once | 42 of 43 |
| Biggest group of identical titles | 3 |
| Titles with a technology list inside them | **19** |
| `normalized_job_title` filled in | 0 of 45 |

45 postings produced 45 different titles. Nothing repeats.

## Why: the titles are being read incorrectly

ITviec shows the title like this:

```
Data Analyst (Azure, SQL, NoSQL, Power BI)
```

The crawler stores it like this:

```
Data Analyst Azure, SQL, NoSQL, Power BI
```

The brackets are dropped, so the list of technologies becomes part of the job name. **19 of 45 titles are affected.**

That means `Data Engineer` and `Data Engineer Java, Python, SQL` are counted as two different jobs, when they are the same job advertised with different tools.

Three worst cases:

| Stored title | What went wrong |
|---|---|
| `Data Engineer English required, /` | Broken — the title is cut off and a separator is left behind |
| `Data Engineer Good English - Up to 75M` | The salary ended up inside the job name |
| `Senior Data Engineer Databricks, SQL, Python, ETL/ELT` | Four technologies inside the job name |

**So any number we publish about "how fragmented job naming is" would be too high, and the error comes from our crawler, not from the market.** We should not report it until the titles are fixed.

## Location

| | |
|---|---|
| Usable (one clear district) | 21 |
| `"Not Available"` | 20 |
| Two values in one field (`"Quận 1, Quận khác"`) | 8 |

Also, the values are districts. RQ1 needs provinces, so these still have to be converted. `normalized_location` is empty for all 45.

---
---

# 3. RQ2 — WHICH SKILLS ARE IN DEMAND

**Field needed:** `extracted_skills`

`extracted_skills` and `skill_count` are empty for all 45 postings. The skill extractor has not been built yet, so **nothing in RQ2 can be checked.**

## What is ready

`job_description` and `job_requirements` are filled in for all 45 postings, and they are kept as two separate fields. That is exactly what the extractor needs to read, and it is in good shape.

## Two things we still cannot check

Both of these decide whether RQ3 results can be trusted, and both need the extractor first:

- **Coverage** — how many postings end up with no skills at all. Target: under 10%.
- **Depth** — how many skills a typical posting produces. Target: at least 3.

If the extractor only finds 1–2 skills per posting, every posting will look different from every other one, and RQ3 will produce a dramatic result for the wrong reason.

---
---

# 4. RQ3 — DO JOB TITLES MATCH THE SKILLS

**Needs:** groups of at least 5 postings sharing a title, plus extracted skills

| | |
|---|---|
| Titles with 5 or more postings | **0** |
| Biggest group | 3 (`data engineer`) |
| Skills extracted | none |

Both halves of RQ3 are stuck. Comparing postings inside one title needs a group of postings — there is none. Comparing one title against another needs two titles to compare — there are none.

## The market is not this fragmented — our crawler is

If the brackets had been kept, the same 45 postings would group like this:

| Job family | Postings |
|---|---|
| Data Engineer | **19** |
| Data Analyst | **8** |
| AI Engineer | **7** |
| ML Engineer | 2 |
| AI Expert / Lead | 2 |
| Data Manager / Leader | 2 |
| Others (including 5 off-topic postings) | 5 |

**Three families have more than 5 postings.**

## What follows from this

**RQ3 needs two things, and both are missing:** groups of at least 5 postings sharing a title, and extracted skills to compare inside those groups. The grouping above shows the first one is ours and fixable now. The second is waiting on the extractor.

**Fixing the crawler is still worth more right now than collecting another 45 postings.** Crawling again without the fix would just produce 45 more unusable titles.

This grouping was done by hand, to show where the problem is. It is not a proposed rule for normalising titles — that is the cleaning stage's job.

---
---

# 5. RQ4 — LET THE ALGORITHM GROUP THE JOBS

**Needs:** extracted skills for at least 300 postings

We have 45 postings and no skills.

With 100–200 possible skills and maybe 5–10 groups, 45 postings is far too few. Any grouping the algorithm found would be chance, and would change every time we re-ran it on a slightly different sample.

The PCA chart is not a separate problem — it draws the result of RQ4, and there is no result to draw.

This stays on hold until the collection reaches the 1,000–2,500 postings the project scope targets.

---
---

# 6. HOW MANY POSTINGS DO WE ACTUALLY HAVE

Five postings do not belong to the project scope, and `relevance_flag` has not been set on any of them:

| job_id | Title | Why it does not belong |
|---|---|---|
| `75437956e1aaafed` | Intern Job Future VPBanker Scholarship 2026 | A scholarship programme, not a job |
| `f2c6a7172480656b` | Advertising Monetization Specialist | Advertising operations |
| `691b9cac78b7c50d` | Internship - BA | Business analyst internship |
| `82f0c2527791a6f5` | Senior SAP Speicialist SAP MM, SD, FICO | SAP consultant |
| `360018923611096a` | AI Automation Engineer Senior/Lead | Uses AI tools; does not build AI |

**The real number of usable postings is 40, not 45.**

Every figure in this report is calculated on 45. Once the flag is set, the analysis stage should work on 40.

Three more are genuinely hard to call and need the leader to decide:

- `f42ffe22ea73beff` — a QA role that tests AI systems
- `752e8906a23eb6e9` — one posting advertising two different jobs
- `1a00e9575f25cfb1` — the posting itself says 70% data work, 30% operations and marketing

---
---

# 7. WHAT NEEDS FIXING

## Collection — Đạt

1. **Keep the brackets when reading the job title.** This is the one fix that unblocks an analysis. Storing the bracket content in its own field would be even better.
2. **Check `Data Engineer English required, /`** — the title came out broken.
3. **Location is missing on 20 of 45 postings.** Also decide what to do when a posting lists two locations: one record with both, or two records.
4. **The experience field is reading the wrong part of the page.** All 45 postings have something in it, but none of it is experience — 37 contain the work arrangement (`At office`, `Hybrid`, `Remote`) and 8 contain a street address. No analysis uses experience, so this is not urgent, but it will be invisible once we have 2,000 postings. The real experience is written inside `job_requirements`.

## Cleaning — Đức

5. **Normalising job titles is the critical path.** The rules have to remove both the seniority word and the technology list. 26 of 45 titles contain a seniority word.
6. **Locations** — convert district to province, and turn `"Not Available"` into `Unknown` rather than leaving it blank.
7. **Set `relevance_flag` and `exclusion_reason`.** Project scope section 7 says excluded postings must be kept and marked with a reason, not deleted.
8. **When the extractor finds no skills, write an empty list, not null.** Null means the extractor never ran, and those are different problems.
9. **Do not match duplicates by title.** The same job appears under different titles on different sites. Compare descriptions instead, or use the employer's own job code — several MB Bank postings start with one, such as `2026TD450985`.

---
---

# 8. CONCLUSION

**Not ready yet. Two things block RQ3, and only one of them is ours to fix now.**

The data structure is sound and every field collection is responsible for is populated. Descriptions and requirements are complete and correctly separated. **The skill extraction step has not been built, so the pipeline has not yet run end to end.**

**Blocking, and fixable now:** technology lists ending up inside job titles, 19 of 45. This is why no title reaches 5 postings.

**Blocking, and not ours:** `extracted_skills` is null on all 45. RQ2 and both halves of RQ3 need it. RQ4 additionally needs around 300 postings.

Fixing the titles alone does not unblock RQ3 — it removes one of the two blockers.

**Next step:** run this check again after the title fix and after skills have been extracted. RQ1 counts and RQ2 skill frequency become checkable then. RQ3 becomes checkable if the title fix produces groups of 5 — and the grouping in section 4 says it should.
