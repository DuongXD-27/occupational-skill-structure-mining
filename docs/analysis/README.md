# ANALYSIS MODULES — HOW TO RUN AND HOW TO READ

Owner: Hồ Nhật Triều (20236003)

Code for RQ2, RQ3 and RQ4. RQ1 belongs to the cleaning stage.

---
---

# PART 1 — RUN IT

## Install

From the repository root:

```powershell
pip install -r requirements-analysis.txt
```

## See all three analyses

```powershell
python scripts/demo_analysis.py
```

Runs on synthetic data and prints every result. Takes about 20 seconds.

## Check the code is correct

```powershell
python -m pytest tests/analysis/ -q
```

Must print `11 passed`.

## Common errors

| Error | Cause |
|---|---|
| `ModuleNotFoundError: No module named 'src'` | Run from the repository root, not from inside a subfolder |
| `ImportError: attempted relative import` | An `__init__.py` is missing in `src/`, `src/analysis/`, `tests/` or `tests/analysis/` |
| Tests hang for a long time | Normal. `compute_stability` refits K-Means 100 times per k |

---
---

# PART 2 — THE ONE IDEA

Everything reduces to a single matrix.

A posting looks like this:

```
job_0000   AI Engineer   [Computer Vision, OpenCV, PyTorch, Python, Jira]
```

It becomes a row of numbers:

```
          AWS  Airflow  Computer Vision  Docker  OpenCV  PyTorch  Python  SQL
job_0000    0        0                1       0       1        1       1    0
```

400 postings become a table of 400 rows by 25 columns, all zeros and ones.
**The three RQ modules read this table and nothing else.**

Reading it down the columns and across the rows asks two different questions:

| Direction | Question | Module |
|---|---|---|
| Columns | Which skills are common, which ones travel together | RQ2 |
| Rows | Which postings resemble which | RQ3, RQ4 |

---
---

# PART 3 — FILE BY FILE

Read in this order. It follows the data, not the alphabet.

## 1. `config.py` — 24 lines

**Problem it solves:** thresholds scattered through the source as magic numbers.

Every number the analysis depends on lives here: 5 postings per title, 3
postings per skill, 300 postings for clustering, 1000 bootstrap rounds, the
random seed. Changing a threshold means editing one line in one file.

Read the whole thing. It is the shortest file and it tells you what the rest
of the code cares about.

## 2. `synthetic.py` — 85 lines

**Problem it solves:** there is no data yet, and real data would not tell you
whether the code is right anyway.

Look at `FAMILIES` at the top. Four job families, each with its own core
skills. **This is the answer key.** `generate_jobs()` builds postings by
drawing from those families and adding noise; `build_matrix()` turns the skill
lists into the 0/1 table.

One detail worth noticing: `Python` appears in three of the four families on
purpose. It is the trap RQ2 has to survive.

## 3. `rq2.py` — 107 lines

**Problem it solves:** confusing "these two skills appear together often" with
"these two skills are related".

Two functions matter.

`compute_cooccurrence` — the whole computation is one line:

```python
C = M.T.values @ M.values
```

Multiplying the matrix by its own transpose gives, for every pair of skills at
once, the number of postings containing both. This replaces two nested loops.
Worth pausing on.

`compute_associations` — three formulas, one line each. Their meaning is
clearest in the output:

```
Airflow – Spark   joint=79   npmi= 0.832     related
Python  – SQL     joint=64   npmi=-0.215     not related
```

Nearly the same raw count; opposite verdicts. Python and SQL meet often only
because both are everywhere.

## 4. `rq3.py` — 119 lines

**Problem it solves:** a dispersion number means nothing on its own.

The hard function is `bootstrap_baseline`. The idea: measuring 0.72 for a
title tells you nothing until you know what a *random* group of the same size
scores. So draw a random group 1000 times, measure each, and compare.

- Title scores clearly below the random range → the title carries information
- Title scores inside the random range → the title is no better than a random label

That verdict is the `informative` column in the output.

The group must be the same size as the title's group. Small groups are always
noisier, so comparing against a differently sized baseline would manufacture a
result.

## 5. `rq4.py` — 156 lines

**Problem it solves:** two ways of cheating, and one way of fooling yourself.

Cheating 1 — putting titles into the model and then announcing that the
algorithm "discovered" job families. Prevented by only ever passing the skill
matrix to `run_clustering`; `test_titles_never_enter_the_feature_matrix`
checks this.

Cheating 2 — looking at the titles before choosing the number of clusters.
Prevented by the function order: `run_clustering` → `select_k` →
`cluster_profiles` → **then** `unblind`.

Fooling yourself — a split that looks clean but disappears when the data
changes. This is what `compute_stability` is for, and it is the hardest
function in the project:

> K-Means labels are arbitrary. Cluster 0 in one run is not cluster 0 in the
> next, so two runs cannot be compared label to label. Instead, draw two
> overlapping 80% subsamples, cluster each, and score the agreement on the
> postings they share using ARI, which ignores what the labels are called.

Also here: `check_minimum_size` refuses to run below 300 postings rather than
producing a picture with no meaning behind it.

## 6. `tests/analysis/test_analysis.py` — 104 lines

**Problem it solves:** not knowing whether any of the above is correct.

Because the synthetic data has a known answer, the tests can assert real
things rather than just "it ran":

- `test_related_pair_beats_common_pair` — PyTorch/OpenCV must score above Python/SQL
- `test_recovers_the_planted_structure` — clustering must find the 4 planted families, ARI above 0.7
- `test_refuses_to_run_below_threshold` — 250 postings must be rejected
- `test_titles_never_enter_the_feature_matrix` — no title may appear as a column
- `test_results_are_reproducible` — two runs must give identical output

## 7. `scripts/demo_analysis.py` — 95 lines

**Problem it solves:** reading code without seeing what it produces.

One command, all output, with the interesting rows pointed out.

---
---

# PART 4 — CHECK YOU UNDERSTOOD

Change something, predict the result, then run `demo_analysis.py`. If the
prediction holds, the understanding is real.

| Change | What should happen |
|---|---|
| Add a fifth family to `FAMILIES` | Chosen k becomes 5 |
| `generate_jobs(noise=0.6)` | Families blur together; silhouette and ARI both fall |
| `MIN_POSTINGS_FOR_CLUSTERING = 500` | RQ4 refuses to run on 400 postings |
| `RANDOM_SEED = 7` | Results barely move. Large movement would mean the code depends on luck |
| Remove `Python` from three families, leave it in one | The Python–SQL pair stops being negative |

The last one is the most informative: it shows the negative association is a
property of the data, not a bug in the code.

---
---

# PART 5 — SWITCHING TO REAL DATA

Only one line changes. Today:

```python
df = synthetic.generate_jobs(n=400)
M = synthetic.build_matrix(df)
```

Once the skill extraction stage delivers its artifact:

```python
M = pd.read_parquet("data/features/job_skill_matrix.parquet")
```

Everything downstream is untouched. The modules never knew where the matrix
came from, which is the point of keeping them separate from the notebook.

---
---

# PART 6 — ONE OPEN QUESTION FOR THE LEADER

`analysis_spec_v0.1.md` states the rule for choosing k as: highest stability →
ties broken by silhouette → within 0.02 stability, take the smaller k.

Those clauses conflict, and the synthetic data exposed it. With 4 families
planted, stability saturates at 1.000 for both k=3 and k=4. Applying only the
last clause picks k=3 and agreement drops to ARI 0.71. Applying the silhouette
clause first picks k=4 — silhouette separates them clearly, 0.41 against
0.54 — and agreement rises to ARI 0.99.

`select_k` currently applies silhouette first. The spec needs rewording to say
so explicitly.
