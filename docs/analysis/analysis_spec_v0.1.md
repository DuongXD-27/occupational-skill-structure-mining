# ANALYSIS SPECIFICATION

Owner: Hồ Nhật Triều (20236003) · Version: v0.1 · Rewritten: 2026-09-24 (wording only — method unchanged)

What this is: the plan for the analysis stage — what we calculate, what comes out, and when a result is safe to publish.

Written before the data arrives on purpose, so the thresholds are set by reasoning and not chosen afterwards to make the numbers look good.

---
---

# 1. THE FOUR QUESTIONS

| | Question | What we do |
|---|---|---|
| RQ1 | What job titles exist, and how common is each? | Count them, measure how scattered the naming is |
| RQ2 | Which skills are in demand, and which go together? | Count skills, count which pairs share a posting |
| RQ3 | Do job titles match the skills asked for? | Same title → different skills? Different titles → same skills? |
| RQ4 | Hide the titles — what groups does the data form? | Cluster on skills only, then compare against the real titles |

RQ4 is the headline. RQ1–RQ3 build up to it.

---
---

# 2. WHAT THE DATA MUST LOOK LIKE

Field names follow `docs/data_schema_v1.md` sections 5, 8 and 13. This spec uses those names exactly — no aliases.

Fields: `job_id` · `raw_job_title` · `normalized_job_title` · `company` · `raw_location` · `normalized_location` · `job_description` · `job_requirements` · `extracted_skills` · `skill_count` · `relevance_flag` · `source` · `source_url` · `crawl_timestamp`

Not every question uses all of them — RQ2 needs only `job_id` and `extracted_skills`.

## Four rules for `extracted_skills` and `raw_job_title`

| Rule | Why |
|---|---|
| `extracted_skills` is a list, not one string | A string has to be split later, and a skill name containing a comma breaks the split |
| It holds taxonomy codes, not the raw words | `sklearn` and `scikit-learn` arriving separately splits one skill into two and hides its real demand |
| Found nothing → empty list, never null | Empty list = posting is badly written. Null = extractor never ran. Different problems, different fixes |
| `raw_job_title` is never overwritten | RQ1 counts distinct raw titles; overwriting destroys the measurement (also scope §10) |

---
---

# 3. RQ1 — WHAT JOB TITLES EXIST

| Metric | Why |
|---|---|
| Postings kept after cleaning | Every percentage later divides by this |
| Distinct raw titles / distinct normalized titles | How many names before and after tidying (raw = trim + lowercase only) |
| Compression ratio = normalized ÷ raw | Low → the variety was just formatting. Near 1 → employers really use that many names |
| Concentration | Do a few titles absorb most postings? |
| Entropy | Same thing from the other side — high means demand is spread evenly. Both reported so they cross-check |
| Rare title rate (≤2 postings) | Rare titles are usually one employer's invention |
| Companies behind those rare titles | 50 odd titles from 3 firms means *"a few firms invent names"*, not *"the market is fragmented"*. Without this the conclusion is wrong |

Output — 3 tables: summary · top 20 titles · rare titles with company and URL.
2 charts: bar chart of top 20 · rank-frequency on log axes.

---
---

# 4. RQ2 — WHICH SKILLS ARE IN DEMAND

| Metric | Why |
|---|---|
| Skill frequency | The most practical question in the project — what should someone actually learn? |
| Skills per posting (mean, median, p10, p90) | Health check on the extractor. Mean of 2 means extraction is broken and everything downstream is wrong |
| Co-occurrence count | Skills travel together — a posting wanting PyTorch usually wants CUDA |

Then three ways to judge whether a pair is really linked or just both common:

| Measure | What it does | Weakness |
|---|---|---|
| Lift | How much more often the pair appears than if unrelated | Inflates rare pairs |
| Normalized PMI | Same idea, rescaled to −1…1 | — |
| Jaccard | Shared postings ÷ postings with either | Biased towards common pairs |

All three, because each fails differently. A pair strong under all three is real.

Skill communities: build a network from the pairs and let it split into areas on its own, instead of grouping skills by hand.

Output — 4 tables: skill frequency · top 30 pairs per measure · communities · negatively associated pairs.
3 charts: top 30 skills · association heatmap · co-occurrence network.

---
---

# 5. RQ3 — DO TITLES MATCH THE SKILLS

## Check 1 — same title, different skills?

Compare every pair of postings sharing a title, measure how different they are. High → the name carries little information.

A raw number here means nothing. 0.62 tells you nothing on its own. So for each title we draw a random group of the same size from the whole corpus, measure its dispersion, repeat 1,000 times. If the real title lands inside that random range, the title is no better than a random label. Same size matters — small groups are always noisier.

## Check 2 — different titles, same skills?

Build a profile per title (average skill pattern of its postings), compare profiles. High similarity → two names describing one job.

Output — 4 tables: dispersion per title with baseline · similar title pairs with shared and distinguishing skills · flagged pairs at three thresholds · title profiles.
3 charts: dispersion vs baseline · title dendrogram · title-by-title heatmap.

---
---

# 6. RQ4 — LET THE ALGORITHM GROUP THE JOBS

Cluster on skills only, titles hidden. Then put titles back and score the agreement.

Near 1 → the data reproduces the titles employers already use.
Near 0 → titles and actual work have come apart.

Either answer is a result. This is the number the report is built around.

## Choosing the number of groups

Sweep k from 2 to 15, score each three ways:

- Silhouette — how cleanly separated. Higher better.
- Davies-Bouldin — spread inside vs distance between. Lower better.
- Stability — recluster a random 80% of the data, 100 times, check whether the same postings stay together.

Rule: highest stability → ties broken by silhouette → within 0.02 stability, take the smaller k.

Stability outranks the rest on purpose. A split can look clean and still vanish on resampling — and if it vanishes, it belongs to this sample, not to the market.

Publish the whole sweep, not just the winner, so a reader can check the choice instead of trusting it.

## Two rules that keep this honest

Blinding. Cluster labels are written to file and committed *before* titles are joined back. Once you can see the titles, you can no longer choose k honestly.

`skill_group` is not an input. The hand-assigned group column is only for comparison. Feeding it in would be circular — grouping by hand, then "discovering" those groups.

Output — 5 tables: sweep across k · cluster profiles · cluster × title table · agreement scores · example postings per cluster.
4 charts: sweep · PCA by cluster · PCA by title · cluster × title heatmap.

The two PCA charts go side by side. An agreement score is hard to feel; two pictures that disagree are understood instantly — and the difference between them *is* the answer to RQ4.

---
---

# 7. THRESHOLDS

| Threshold | Value | Reason |
|---|---|---|
| Postings per title (RQ3) | ≥ 5 | 5 postings give 10 pairs. Below that the average can't be told apart from chance |
| Postings per skill | ≥ 3 | Below 3 a skill is noise |
| Joint appearances per pair | ≥ 5 | Lift swings wildly below this — one lucky co-occurrence gives an extreme value |
| Skills per posting (similarity) | ≥ 2 | One skill gives nothing to compare. Still counted in skill frequency, dropped only from similarity and clustering |
| Postings for clustering | ≥ 300 | Any grouping found below this is chance |

All five are my proposal and still provisional — they need the leader's approval and will be revisited once the real corpus size is known. Changes go in v0.2 with the reason.

---
---

# 8. WHAT WE CANNOT RUN ON THE SAMPLE

On 30–50 postings.

Can run, but only as a pipeline test — never as findings: posting counts, title counts, skill frequency, skills per posting, the quality checks.

| Cannot run | Why |
|---|---|
| Concentration, entropy, rare titles | Need a real distribution. At 40 postings almost every title appears once |
| Skill pair analysis | Almost no pair reaches 5 joint appearances |
| RQ3, both checks | Almost no title reaches 5 postings; a profile from 1–2 postings is just those postings |
| All of RQ4 | 40 postings against a minimum of 300 |

Removed completely, not published with a warning. A number published with a caveat still gets quoted as a number.

---
---

# 9. QUALITY CHECKS AND REPRODUCIBILITY

Eight quality checks run before any analysis. A failure sends the work back to collection or cleaning, not into a chart.

Why this matters: a weak extractor produces short skill lists → short lists make every posting look different → that inflates dispersion and weakens every association. A technical fault would manufacture exactly the conclusion we expect, instead of testing it.

Reproducibility: one fixed seed, all thresholds in one config file, every result table headed with corpus size and spec version — so every number states how much data it stands on.

---
---

# 10. QUESTIONS FOR THE TEAM

1 — Leader. The important one. Does `Senior Data Analyst` count as `Data Analyst`? If kept separate, many titles fall below 5 postings and RQ3 loses most of its sample.

2 — Taxonomy owner. How many skills in taxonomy v0.1? Drives the skill threshold and the 300-posting minimum.

3 — Taxonomy owner. Will there be a `skill_group` column? Section 6 uses it for comparison only.

4 — Collection owner. Answered by the sample: `job_description` and `job_requirements` are separate and populated on all 45. Remaining question: `relevance_flag` and `exclusion_reason` are null on all 45 — does collection set them, or cleaning?

5 — Leader. Add a title-prediction model as an extra RQ3 measure? It would reduce RQ3 to one headline number. Not in scope §11, not proposed to jump the priority order in §12 — raised for a decision, not assumed.
