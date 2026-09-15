# ANALYSIS SPECIFICATION V0.1

**Owner:** Hồ Nhật Triều (20236003)

**Version:** v0.1

**Date:** 2026-09-15

---

---

# 1\. RESEARCH QUESTION TO ANALYSIS

## RQ1 — Observed Market Structure

**Question**

What job titles exist in the collected data, and how common is each?

**Analysis**

Count titles, then measure how fragmented the naming is.

---

## RQ2 — Skill Demand and Structure

**Question**

Which skills are demanded most, and which skills appear together?

**Analysis**

Skill frequency, then pairwise co-occurrence.

---

## RQ3 — Titles Against Skills

**Question**

Do job titles reflect the skills employers actually ask for?

**Analysis**

Two directions, run separately:

1. Same title, different skills  
2. Different titles, same skills

---

## RQ4 — Data-Driven Structure

**Question**

With titles hidden, what groups emerge from the skills alone?

**Analysis**

Cluster the postings on skills only, then compare the clusters against the real titles.

---

---

# 2\. INPUT FIELDS

## Required Fields

- `job_id`  
- `raw_job_title`  
- `normalized_job_title`  
- `company`  
- `location`  
- `description`  
- `requirements`  
- `skills_extracted`  
- `source`  
- `source_url`  
- `crawl_date`

Each research question uses a subset.

- RQ2 needs only `skills_extracted` and `job_id`  
- RQ1 additionally needs `company` and `location`

---

## Rule 1 — `skills_extracted` must be a list

**Not** a delimited string.

A string has to be split later, and any skill name containing a comma breaks the split.

---

## Rule 2 — `skills_extracted` must hold taxonomy codes

**Not** raw surface text.

If `sklearn` and `scikit-learn` arrive as two separate values, one skill is split across two columns and its demand appears smaller than it is.

---

## Rule 3 — An empty result is an empty list, never null

We must be able to separate two different situations:

- extraction ran and found nothing → the posting is badly written  
- extraction did not run → the code has a bug

They require different fixes.

---

## Rule 4 — `raw_job_title` is never overwritten

RQ1 counts how many distinct raw titles exist.

Overwriting the field destroys the measurement. Already required by `project_scope_v1.md` section 10\.

---

---

# 3\. METRICS

## 3.1 RQ1 Metrics

### Postings retained

**How:** count of postings kept after cleaning.

**Why:** every share reported later is divided by this number.

---

### Distinct raw titles, and distinct normalized titles

**How:** two separate counts. Raw titles are counted after trimming whitespace and lowercasing only.

**Why:** shows how many different names the market uses, before and after tidying.

---

### Compression ratio

**How:** normalized title count divided by raw title count.

**Why:** a low ratio means the variety was only formatting. A ratio near 1 means the market genuinely uses many different names.

---

### Concentration

**How:** sum of the squared share of each title.

**Why:** a high value means a few titles absorb most postings.

---

### Entropy

**How:** entropy of the title distribution, rescaled to 0–1.

**Why:** a high value means demand is spread evenly. Reported together with concentration so the two cross-check each other.

---

### Rare title rate

**How:** share of normalized titles appearing in 2 postings or fewer.

**Why:** rare titles are usually invented by a single employer.

---

### Companies behind rare titles

**How:** number of distinct firms posting those rare titles.

**Why:** if 50 unusual titles come from 3 firms, the correct finding is "a few firms invent names", not "the market is fragmented". Without this check the conclusion is wrong.

---

## 3.2 RQ2 Metrics

### Skill frequency

**How:** number and share of postings containing each skill.

**Why:** the most basic question in the project — what should a candidate actually learn?

---

### Skills per posting

**How:** mean, median, 10th and 90th percentile.

**Why:** if the mean is only 2, extraction is broken and every downstream result is wrong.

---

### Co-occurrence count

**How:** for each skill pair, the number of postings containing both.

**Why:** skills travel together. A posting asking for PyTorch usually asks for CUDA too.

---

### Lift

**How:** observed joint frequency divided by the frequency expected if the two skills were unrelated.

**Why:** good at surfacing surprising pairs, but it inflates rare ones.

---

### Normalized PMI

**How:** the same association idea, rescaled to the range −1 to 1\.

**Why:** bounded, so pairs with very different frequencies stay comparable.

---

### Jaccard

**How:** shared postings divided by postings containing either skill.

**Why:** the most conservative of the three, and biased towards common pairs. Three measures are used because each one fails differently.

---

### Skill communities

**How:** community detection on the skill co-occurrence graph.

**Why:** lets the data divide skills into areas, instead of us dividing them by hand.

---

## 3.3 RQ3 Metrics

### Intra-title dispersion

**How:** 1 minus the mean Jaccard across every pair of postings sharing a title.

**Why:** high dispersion means postings with the same name demand different skills — so the name carries little information.

---

### Inter-title cosine similarity

**How:** cosine between title profiles. A title profile is the average skill vector of all postings with that title.

**Why:** high similarity means two different names are describing the same job.

---

## 3.4 RQ4 Metrics

### Silhouette, Davies-Bouldin, stability

**How:** three cluster-quality scores computed for every candidate number of clusters.

**Why:** they let us choose the number of clusters by rule rather than by eye.

---

### ARI and NMI

**How:** agreement between the cluster labels and the normalized titles.

**Why:** near 1 means the data reproduces existing titles; near 0 means titles and real work are unrelated. This is the project's headline number.

---

---

# 4\. RESULT TABLES — 16 TOTAL

Tables are specified now so that at run time we only fill in numbers, rather than redesigning the output.

## RQ1 — 3 tables

1. Summary — postings, title counts, compression ratio, concentration, entropy, rare rate, date window  
2. Top 20 normalized titles  
3. Rare titles, with company and source URL

---

## RQ2 — 4 tables

1. Skill frequency  
2. Top 30 skill pairs, under each of the three measures  
3. Skill communities  
4. Negatively associated pairs

---

## RQ3 — 4 tables

1. Dispersion per title, with its random baseline  
2. Similar title pairs, with shared and distinguishing skills  
3. Flagged pair counts at three thresholds  
4. Title profiles

---

## RQ4 — 5 tables

1. Cluster sweep across k  
2. Cluster profiles  
3. Cluster by title contingency table  
4. ARI and NMI summary  
5. Representative postings per cluster

---

---

# 5\. CHARTS — 13 TOTAL

## RQ1 — 2 charts

1. Horizontal bar chart of the top 20 titles  
2. Rank-frequency plot on log axes

---

## RQ2 — 3 charts

1. Bar chart of the top 30 skills  
2. Association heatmap  
3. Skill co-occurrence network

---

## RQ3 — 3 charts

1. Dot plot of dispersion per title, with the random baseline behind each point  
2. Title dendrogram  
3. Title by title similarity heatmap

---

## RQ4 — 4 charts

1. Cluster sweep across k  
2. PCA scatter coloured by cluster  
3. PCA scatter coloured by title  
4. Cluster by title heatmap

**Charts 2 and 3 are placed side by side.**

The ARI number is hard to feel. Two panels that disagree are understood at a glance. The difference between them is the answer to RQ4.

---

---

# 6\. MINIMUM THRESHOLD FOR SIMILARITY ANALYSIS

## Main threshold — a title needs at least 5 postings

5 postings produce 10 pairs to compare.

Below 5 there are fewer than 10 pairs, the average becomes too noisy, and the result cannot be separated from chance.

---

## Supporting threshold — a skill needs at least 3 postings

Below 3 appearances, a skill contributes noise and no reliable signal.

---

## Supporting threshold — a skill pair needs at least 5 joint appearances

Below that, lift swings wildly.

A pair observed once can produce an extreme value purely by luck.

---

## Supporting threshold — a posting needs at least 2 skills

One skill gives nothing to compare against.

Such postings are still counted in skill frequency; they are excluded only from similarity and clustering.

---

## Status of these numbers

All four are **provisional**.

They will be revisited once the real corpus size is known, and any change is recorded in v0.2 together with its reason.

---

---

# 7\. CLUSTERING EVALUATION CRITERIA

## What is measured

Sweep the number of clusters from 2 to 15\. For each value, measure three things.

### Silhouette

How cleanly the clusters separate from each other. Higher is better.

### Davies-Bouldin

Ratio of within-cluster spread to between-cluster distance. Lower is better.

### Stability

Resample 80% of the corpus, cluster again, repeat 100 times, and check whether the same postings stay together.

---

## Selection rule

Applied in this order:

1. Take the number of clusters with the highest stability  
2. Break ties using silhouette  
3. If two candidates are within 0.02 stability of each other, take the smaller number

---

## Why stability outranks silhouette

A split can look very clean and still disappear when the data is resampled.

If it disappears, it is a property of this particular sample, not of the market.

---

## Publication requirement

Publish the entire sweep, not only the chosen number.

This lets a reader check the selection instead of trusting it.

---

---

# 8\. ANALYSES DROPPED AT SAMPLE SCALE

Applies to the 30–50 posting sample.

## Can be run — as a pipeline test, not as findings

- Posting counts  
- Raw and normalized title counts  
- Skill frequency and skills per posting  
- All eight data quality checks

---

## Dropped — concentration, entropy, rare titles

These need a title distribution with real mass. At 40 postings almost every title is a singleton.

---

## Dropped — skill pair analysis

Almost no pair reaches 5 joint appearances.

---

## Dropped — same title, different skills

Almost no title reaches 5 postings.

---

## Dropped — different titles, same skills

A title profile built on 1 or 2 postings is simply those postings.

---

## Dropped — all of RQ4

40 postings against a minimum of 300\.

---

## How they are dropped

**Removed completely, not reported with a warning.**

A number published with a caveat still gets quoted as a number.

The sample exists to confirm that the fields are present and correctly formatted, not to produce conclusions about the market.

---

---

# 9\. ADDITIONS BEYOND THE REQUIRED SCOPE

## ① Random baseline for RQ3

**What**

For each title, draw a random group of the same size from the whole corpus, measure its dispersion, and repeat 1000 times.

**Why**

A dispersion of 0.62 means nothing on its own. If the title's value falls inside the random range, the title carries no information at all.

**Note**

The random group must match the title's size, because small groups are always noisier.

---

## ② Blinding procedure for RQ4

**What**

Write cluster labels to file and commit them before joining titles back in.

**Why**

Once titles are visible, the number of clusters can no longer be chosen honestly.

---

## ③ `skill_group` is not a clustering input

**What**

The manually assigned skill group column is used only for comparison against the discovered communities.

**Why**

Feeding it in would be circular — assigning groups by hand, then "discovering" those same groups.

---

## ④ Eight data quality checks

**What**

Run before any analysis. A failure sends the work back to collection or cleaning.

**Why**

Weak extraction produces short skill lists. Short lists make every posting look different. That inflates dispersion and weakens every association.

**Consequence**

A technical fault would manufacture the conclusion we expect, instead of testing it.

---

## ⑤ Reproducibility

**What**

Fixed random seed. All thresholds in one config file. Every result table carries a header with corpus size and spec version.

**Why**

So the same run reproduces later, and every number states how much data it stands on.

---

## ⑥ Five questions for the team

Addressed to specific people rather than to the group.

**Question 1 — Leader (most important)**

Does `Senior Data Analyst` count as `Data Analyst`?

If kept separate, many titles fall below the 5-posting threshold and RQ3 loses most of its sample.

**Question 2 — Taxonomy owner**

How many skills will taxonomy v0.1 contain? This drives the skill threshold and the 300-posting clustering minimum.

**Question 3 — Taxonomy owner**

Does the taxonomy include a `skill_group` column? Section 9 ③ uses it for comparison only.

**Question 4 — Collection owner**

Are description and requirements separate at the source, or merged? The quality checks need to know which field may legitimately be empty.

**Question 5 — Leader**

Should we add a title-prediction model as an extra RQ3 measure? It would reduce RQ3 to a single headline number.

It is not in `project_scope_v1.md` section 11, and it is not proposed to jump the optional priority order in section 12\. Raised for a decision, not assumed.

---

---

# 10\. CHANGELOG

**v0.1** — 2026-09-15 — First version.

&nbsp;