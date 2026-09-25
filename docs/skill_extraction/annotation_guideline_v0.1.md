# Skill Annotation Guideline v0.1

**Project:** Vietnam Data & AI Job Skill Landscape 2026  
**Vietnamese title:** Khám phá cấu trúc nghề nghiệp và nhu cầu kỹ năng Data/AI tại Việt Nam năm 2026 từ dữ liệu tuyển dụng trực tuyến tự thu thập  
**Version:** v0.1  
**Annotation date:** 2026-09-15  
**Status:** Pilot / draft for supervisor review

---

## 1. Purpose

This document defines **what counts as a technical skill** in this project and how different surface forms referring to the same skill should be normalized.

The guideline is intended to make the annotation process:

- **Consistent:** the same type of case should be handled in the same way across job descriptions (JDs).
- **Reproducible:** another annotator should be able to read the guideline and make similar decisions.
- **Interpretable:** each skill should be included or excluded according to an explicit rule.
- **Aligned with RQ2–RQ4:** skill-based representations should be created without imposing a predefined occupational taxonomy.

> **Important note:** `skill_group` in the taxonomy is only a vocabulary-management category. It is **not an occupational taxonomy** and must not be used to force job postings into predefined occupations before clustering.

---

## 2. Official Sample Used for v0.1 Counts

The authoritative sample is `data/sample/sample_jobs.jsonl`, containing **45 unique job descriptions**, all from **ITviec**. This is the ground-truth sample prepared in PR #3 and is the only corpus used to calculate `observed_count` in `skills_taxonomy_v0.1.csv`.

CareerViet records are not part of this sample. The approved source scope uses ITviec as the primary source and TopCV only as a fallback.

The taxonomy contains **246 canonical skills**, and every retained skill appears in at least one JD in the official 45-JD corpus. Of these, **102 skills appear in exactly one JD**, and **150 skills appear in at most two JDs**. Skills with an `observed_count` of zero are excluded because they are not evidenced by the official sample.

### Interpreting `observed_count`

`observed_count` in `skills_taxonomy_v0.1.csv` represents **document frequency**:

> the number of unique JDs in the official 45-record ITviec sample that explicitly mention the skill at least once.

If a skill appears five times within the same JD, it still contributes only **1** to the count. Canonical names, abbreviations, and aliases are mapped to the same canonical skill before counting.

**The `observed_count` values must not be interpreted as market-wide demand shares for Vietnam**, because this is a small taxonomy-validation sample from one source.

---

## 3. Definition of a “Technical Skill”

In this project, a **technical skill** is:

> **A learnable capability, method, tool, language, framework/library, platform, data system, analytical technique, or technical domain that is explicitly mentioned in a JD as part of performing Data/AI work.**

An item does not need to be a software product or tool to count as a skill. Methods such as `Machine Learning`, `ETL`, `Data Modeling`, `A/B Testing`, `Feature Engineering`, `RAG`, or `MLOps` are also retained when they are mentioned in a professional/technical context.

---

## 4. Scope Decisions for v0.1

| Information type | Decision | Examples |
|---|---|---|
| Programming/query languages | **INCLUDE** | Python, SQL, Java, C++, R |
| Frameworks/libraries | **INCLUDE** | PyTorch, TensorFlow, Pandas, scikit-learn, LangChain |
| Databases/data platforms | **INCLUDE** | PostgreSQL, MongoDB, BigQuery, Databricks |
| Cloud platforms/services | **INCLUDE** | AWS, Azure, GCP, S3, SageMaker, Vertex AI |
| DevOps/MLOps tooling | **INCLUDE** | Docker, Kubernetes, MLflow, Kubeflow, CI/CD |
| High-level technical methods | **INCLUDE if sufficiently specific and operational** | Machine Learning, NLP, Computer Vision, ETL, Data Modeling, MLOps |
| Statistical/analytical methods | **INCLUDE** | A/B Testing, Regression, Forecasting, Hypothesis Testing |
| Technical data/AI architectures | **INCLUDE** | Data Lakehouse, RAG, Event-Driven Architecture, Multi-Agent Systems |
| Data formats when technically required | **INCLUDE** | JSON, Parquet, XML |
| Soft skills | **EXCLUDE** | communication, teamwork, leadership, problem solving |
| Personality traits | **EXCLUDE** | proactive, hard-working, ownership, curiosity |
| Human languages | **EXCLUDE from the technical taxonomy** | English, Japanese |
| Education/certification requirements alone | **EXCLUDE** | Bachelor's degree, TOEIC; a certification is retained only if the technology named within it is also an independent skill |
| Years of experience/seniority | **EXCLUDE** | 3+ years, Senior, Lead |
| Job/occupation labels | **EXCLUDE** | Data Engineer, Data Scientist, AI Engineer |
| Overly broad umbrella labels | **EXCLUDE by default** | AI, Technology, Data |
| Company/product marketing text | **EXCLUDE** unless it is a requirement/responsibility of the role | technology mentioned only as part of the company's product or culture |

### Distinguishing Role Labels from Competencies

- `Data Engineer` in a job title → **not a skill**.
- `Data Engineering` used only as an occupation/specialization label → **do not automatically annotate**.
- `Data Analysis` in a statement such as “perform data analysis” or “strong data analysis skills” → **may be annotated**, because it describes a concrete capability.
- `AI` on its own → too broad, **do not include in taxonomy v0.1**.
- `Generative AI`, `Machine Learning`, `Computer Vision`, `NLP` → sufficiently specific to retain.

---

## 5. Text Regions Used for Annotation

### INCLUDE

Prioritize the following sections:

1. `Requirements`
2. `Responsibilities`
3. `Nice to have / Preferred`
4. Employer-provided `Skills` tags for the specific vacancy
5. The job title **only when the title explicitly contains a technology/skill**, e.g. `Data Engineer (Python, Kafka)`.

### EXCLUDE

Do not include a skill solely because it appears in:

- general company descriptions;
- benefits;
- company culture or advertised tools unrelated to the specific role;
- similar-job lists;
- navigation/footer content;
- the occupation title itself.

If a technology appears in marketing text **and** is also explicitly mentioned as a requirement or responsibility of the role, annotate it based on the role-specific section.

---

## 6. Required vs. Nice-to-Have Skills

In v0.1, **both required and preferred/nice-to-have skills are counted**, because the current goal is **taxonomy induction**: discovering the vocabulary of skills used by the market.

However, for the formal demand analysis, additional fields should be stored, such as:

- `requirement_level = required`
- `requirement_level = preferred`
- `requirement_level = responsibility/context`

This prevents mandatory and optional skills from being treated as equivalent.

---

## 7. Abbreviation Rules

The taxonomy CSV uses the following schema:

```text
skill_id,canonical_name,abbreviation,aliases,skill_group,observed_count
```

`abbreviation` stores standard shortened forms of the canonical name. `aliases` stores other spelling, wording, spacing, or naming variants; abbreviations must not be duplicated in `aliases`. Multiple values in either field are separated by `; `.

Example:

```text
canonical_name = Natural Language Processing
abbreviation = NLP
aliases = text processing; xử lý ngôn ngữ tự nhiên
```

### 7.1. Standard, Unambiguous Abbreviations

Map them to a canonical skill:

- `ML` → `Machine Learning`
- `DL` → `Deep Learning`
- `NLP` → `Natural Language Processing`
- `LLM`, `LLMs` → `Large Language Models`
- `RAG` → `Retrieval-Augmented Generation`
- `MCP` → `Model Context Protocol`
- `AWS` → `Amazon Web Services`
- `GCP` → `Google Cloud Platform`
- `OCR` → `Optical Character Recognition`
- `MLOps`, `ML Ops`, `MLops` → `MLOps`
- `ETL` and `ELT` are **two different skills** and must not be merged.

### 7.2. Ambiguous Abbreviations: Map Only When Context Is Sufficient

For example, `CV` may mean:

- `Computer Vision`, or
- curriculum vitae.

Map `CV` → `Computer Vision` only when the technical context confirms the meaning, for example when it appears with `OpenCV`, image/video models, object detection, or an explicit mention of Computer Vision.

### 7.3. Do Not Infer Unmentioned Acronyms or Concepts

If a JD writes `Retrieval-Augmented Generation`, normalize it to the RAG concept. However, if the JD does not mention that concept, do not infer it simply because the role uses LLMs.

---

## 8. Synonym and Spelling Normalization

Variants that differ only in capitalization, spacing, hyphenation, or common naming conventions should be mapped to the same canonical item.

Examples:

- `Postgres`, `Postgre SQL` → `PostgreSQL`
- `PowerBI` → `Power BI`
- `sklearn`, `scikit learn` → `scikit-learn`
- `MS SQL Server`, `MSSQL` → `Microsoft SQL Server`
- `K8s` → `Kubernetes`
- `GenAI` → `Generative AI`

Do not merge two technologies simply because they frequently co-occur.

Examples:

- `PyTorch` ≠ `TensorFlow`
- `AWS` ≠ `Azure`
- `Data Lake` ≠ `Data Warehouse`
- `RAG` ≠ `Vector Database`
- `ETL` ≠ `ELT`

---

## 9. Parent–Child Technology Rule

Do not automatically infer parent or child skills.

Examples:

- JD mentions only `SageMaker` → annotate `Amazon SageMaker`; **do not automatically add AWS**.
- JD explicitly writes `AWS SageMaker` → both `Amazon Web Services` and `Amazon SageMaker` are treated as explicit.
- JD mentions `Kubernetes` → do not infer `Docker`.
- JD mentions `LangChain` → do not infer `RAG`.
- JD mentions `LLM` → do not infer `Prompt Engineering`.

Reason: the project aims to measure **what employers actually write**, not what the annotator believes a candidate would “obviously need to know.”

---

## 10. Implicit Skill Rule

**Default rule: DO NOT annotate implicit skills in v0.1.**

Examples:

- “Build dashboards” → annotate `Dashboarding`; **do not infer Power BI/Tableau**.
- “Deploy models to production” → may annotate `Model Deployment`; **do not infer Docker/Kubernetes/AWS**.
- “Build recommendation systems” → annotate `Recommendation Systems`; **do not infer Python/PyTorch**.
- “Work with relational databases” → annotate `Relational Databases`; **do not infer PostgreSQL/MySQL**.

The rule-based extractor and gold annotation should be grounded in evidence explicitly present in the text.

---

## 11. Composite Mentions and Alternatives

If a JD clearly lists multiple technologies using `/`, `or`, or `and`, annotate each technology separately.

Examples:

- `C/C++` → `C` + `C++`
- `PyTorch/TensorFlow` → `PyTorch` + `TensorFlow`
- `AWS/GCP/Azure` → three cloud skills
- `Airflow, Dagster or Prefect` → three skills

This applies even when the JD says “one of”.

---

## 12. Context-Dependent Cases

### 12.1. Applied Business/Analytics Skills

Applied use cases are retained **when the role requires the employee to build, model, or analyze them as a technical capability**, for example:

- Fraud Detection
- Risk Scoring
- Credit Scoring
- Customer Analytics
- Cohort Analysis
- Dynamic Pricing

Do not retain them if the phrase only describes a business domain or general business objective.

### 12.2. Data Governance / Quality / Security

Retain these when the JD requires the employee to implement, design, or perform them:

- Data Governance
- Data Quality
- Data Validation
- Data Security
- Data Lineage

Do not retain generic legal/compliance terminology unless it represents a concrete technical task.

### 12.3. Cloud

- `AWS`, `Azure`, `GCP` → retain.
- `cloud` → retain under the canonical skill `Cloud Computing` only when the JD requires cloud knowledge/experience.
- “cloud company / cloud product” in a company description → do not retain.

### 12.4. Generic Software Practices

Clearly technical capabilities such as `API Design`, `Microservices`, `CI/CD`, `Observability`, and `Debugging` are retained.

Soft/management practices such as stakeholder management, mentoring, communication, and ownership are not part of the v0.1 technical taxonomy.

---

## 13. Counting Rule

For each JD:

1. Normalize the raw mention → canonical skill.
2. Deduplicate within the same JD.
3. Each canonical skill receives a 0/1 value for that JD.
4. `observed_count` = total number of JDs with value 1.
5. Exact duplicate postings are counted only once.

Counts are generated from `raw_job_title`, `job_description`, and `job_requirements` in the official sample. When a shorter term overlaps a longer explicit taxonomy term, the longer term wins; for example, `BI` inside `Power BI` does not independently increment `Business Intelligence`. Context-sensitive abbreviations and short language names are handled conservatively to avoid matches such as `CV` meaning curriculum vitae, `R` inside `R&D`, or `Go` in ordinary prose.

Run `python scripts/recount_taxonomy.py` from the repository root to reproduce the taxonomy counts and remove skills that are not observed in the official sample.

Example: if one JD mentions `Python` eight times:

```text
Python document count = 1
```

If three JDs respectively use `Postgres`, `PostgreSQL`, and `Postgre SQL`:

```text
canonical = PostgreSQL
observed_count = 3
```

---

## 14. Skill Groups v0.1

The groups in the CSV are used to organize the vocabulary:

- Programming & Query Languages
- Data Analysis & BI
- Data Engineering & Architecture
- Distributed, Streaming & Big Data
- Databases, Storage & Data Formats
- Cloud Platforms & Services
- DevOps, MLOps & Infrastructure
- Machine Learning, Statistics & Optimization
- Generative AI & Agentic Systems
- NLP, Vision & Multimodal AI
- Software Engineering & APIs
- Data Quality, Testing & Observability
- Security Engineering
- Applied Analytics & Business Platforms
- Engineering Tools & Collaboration

**Do not use these groups as occupational labels in RQ4.** Occupational clustering must still be based on the skill representation of each job posting.

---

## 15. Pilot Sanity Check

Top 10 canonical skills by `observed_count` in the official 45-JD ITviec sample:

| Rank | Canonical skill | JD count |
|---:|---|---:|
| 1 | Python | 31 |
| 2 | Data Pipelines | 23 |
| 3 | SQL | 23 |
| 4 | Cloud Computing | 21 |
| 5 | Data Quality | 20 |
| 6 | Machine Learning | 19 |
| 7 | Amazon Web Services | 17 |
| 8 | ETL | 17 |
| 9 | CI/CD | 16 |
| 10 | Business Intelligence | 15 |

This table is only a **sanity check for the pilot taxonomy**, not an official RQ2 result.

---

## 16. Recommended Annotation Workflow for Future Batches

1. Read the JD and highlight raw technical mentions.
2. Apply the include/exclude rules before consulting the taxonomy.
3. If the concept already exists in the taxonomy → map it to `canonical_name`.
4. If the concept is new and valid → add a new canonical skill and append a new `skill_id`.
5. Record a new alias if the mention is only a variant of an existing skill.
6. Do not add implicit skills.
7. Deduplicate skills within each JD before incrementing counts.
8. Flag uncertain cases for review instead of guessing.
9. Periodically review singleton/rare skills to detect:
   - typos;
   - aliases that have not yet been merged;
   - items that are overly granular;
   - business phrases incorrectly classified as technical skills.

---

## 17. Decisions to Review in v0.2

After annotating more data, revisit whether:

- all data formats (`CSV`, `XML`, `JSON`) should remain separate skills;
- platforms and services should be represented at multiple hierarchical levels;
- low-frequency applied use cases should be retained;
- a formal `parent_skill_id` hierarchy should be introduced;
- `requirement_level` and `evidence_span` should be added;
- a minimum document-frequency threshold is needed for downstream modeling.

**Do not remove a singleton simply because it is rare during taxonomy induction.** Pruning should happen only after checking whether the singleton is a genuine skill, an unmerged alias, or noise.

---

## 18. Relationship to the LLM Comparator

If the optional LLM experiment is performed, both the rule-based extractor and the LLM must be evaluated on **the same held-out set, using the same annotation guideline and the same canonical taxonomy**.

The LLM should not receive credit simply for returning a concept that falls outside the defined scope. Predictions must be normalized to the taxonomy before calculating Precision / Recall / F1.

This ensures that the comparison genuinely asks:

> With **the same skill definition and the same corpus**, how much does an LLM improve extraction quality over Dictionary + Regex + Fuzzy matching, and what are the trade-offs in cost, dependency, reproducibility, and interpretability?

---

## 19. Versioning

- `v0.1`: taxonomy counts validated against 45 unique ITviec JDs in `data/sample/sample_jobs.jsonl`.
- When adding new skills, **never reuse an existing `skill_id` for a different concept**.
- Aliases may be expanded, but canonical names should only be changed for a clear reason, with a recorded migration.
- Before using the taxonomy for formal analysis, freeze a version (for example, `v1.0`) and maintain a changelog.
