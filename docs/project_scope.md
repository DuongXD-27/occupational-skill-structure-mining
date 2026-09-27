# PROJECT SCOPE V1

## 1. Project Information

### English Title

Vietnam Data & AI Job Skill Landscape 2026:
Mining Self-Collected Online Job Postings to Discover Occupational and Skill Structure

### Vietnamese Title

Khám phá cấu trúc nghề nghiệp và nhu cầu kỹ năng Data/AI tại Việt Nam năm 2026
từ dữ liệu tuyển dụng trực tuyến tự thu thập.

### Version

v1.0

---

## 2. Research Problem

The recruitment market employs a wide variety of titles for positions related to Data and AI. However, job titles do not necessarily consistently reflect the actual skills demanded by employers.

Two job postings with identical titles may require substantially different skill sets. Conversely, two jobs with distinct titles may demand virtually identical skill profiles.

The project will self-collect Data/AI recruitment postings and investigate the relationships between:

- job titles;
- required skills;
- degree of similarity across jobs;
- occupational clusters emerging directly from data.

The project does not predefine a fixed number of occupational groups.

---

## 3. Objectives

The primary objective of the project is to construct an end-to-end Data Science pipeline applied to real-world recruitment data self-collected by the team.

The project must accomplish the following steps:

1. Collect job postings from public sources.
2. Filter postings genuinely relevant to Data/AI.
3. Clean, normalize, and deduplicate records.
4. Extract skills from job posting content.
5. Evaluate skill extraction performance.
6. Analyze job title structures and skill demand.
7. Measure pairwise similarity between job postings.
8. Discover skill-based job clusters via clustering algorithms.
9. Compare discovered clusters against actual job titles.
10. Present findings, limitations, and empirical conclusions drawn from the data.

---

## 4. Research Questions

### RQ1 — Observed Market Structure

What Data/AI job titles exist in the collected data, and what is their prevalence?

Key aspects to investigate include:

- number of valid job postings;
- count of raw job titles;
- count of normalized job titles;
- most common job titles;
- degree of title fragmentation across the market.

### RQ2 — Skill Demand and Structure

Which technical skills appear most frequently, and which skills frequently co-occur?

### RQ3 — Relationship Between Job Titles and Skill Requirements

Do job titles consistently reflect skill requirements?

The analysis encompasses two directions:

- identical job titles with divergent skill requirements;
- distinct job titles with convergent skill requirements.

### RQ4 — Data-Driven Occupational Structure

Without utilizing job titles as input features, what skill clusters naturally emerge from the postings?

After identifying clusters, the project will compare them against actual job titles to determine whether market naming conventions align with the underlying skill structures.

---

## 5. Target Market Scope

The project focuses on technical positions whose core responsibilities directly relate to one or more of the following domains:

- Data Analysis;
- Business Intelligence;
- Data Engineering;
- Data Science;
- Machine Learning;
- Artificial Intelligence;
- Natural Language Processing;
- Computer Vision;
- Generative AI / LLMs;
- MLOps and related technical AI/Data roles.

The list above defines the data collection boundary only.

It is not an occupational taxonomy and must not be used to force postings into predefined categories.

---

## 6. Inclusion Criteria

A job posting is retained in the research corpus when it satisfies the following criteria:

- Publicly posted on an approved team data source;
- Within the project observation window;
- Core job responsibilities are genuinely technical and relevant to Data or AI;
- Contains a valid job title;
- Contains sufficient description or requirements text to support skill extraction;
- Not an identified duplicate record.

Internship or fresher positions may be retained provided the role genuinely falls within the technical Data/AI scope.

---

## 7. Exclusion Criteria

Postings are excluded from the research corpus if they meet any of the following conditions:

- Contains keywords like “Data” or “AI” but core duties are not technical Data/AI;
- Pure data entry positions;
- Sales, business development, or product marketing for AI products;
- General IT/infrastructure operations roles not performing Data/AI tasks;
- Insufficient text content to determine skill requirements;
- Error pages, broken links, or unreliably scraped data;
- Identified duplicates of an existing vacancy.

Excluded records must not be deleted from the raw dataset; they must be flagged alongside their explicit exclusion reason.

---

## 8. Data Source Scope

### Final Source Selection

- Primary source: ITviec;
- Backup source: TopCV.

ITviec is the official primary source and is used for normal dataset collection. Sample data, taxonomy, data-quality checks, and downstream analysis must be traceable to the primary dataset unless the project explicitly approves another dataset.

TopCV is a fallback source. It is activated only if ITviec becomes inaccessible, technically unusable, cannot provide sufficient valid records, or otherwise cannot satisfy the collection target. The selection of TopCV as a backup does not make the project an automatically combined multi-source dataset.

If TopCV is activated, its records must satisfy the same inclusion and exclusion criteria, follow the same data schema and data-quality rules, and preserve the `source` and `source_url` provenance fields so downstream analysis can distinguish records by source.

Prior to large-scale data collection, the team must verify:

- Terms of Service;
- robots.txt;
- Login / authentication requirements;
- Access rate limits;
- Restrictions on automated scraping;
- Terms governing data reuse and publication;
- Technical characteristics and stability of the platform.

If ITviec proves unfeasible under the conditions above, the team pivots to TopCV.

If both prove unfeasible, the team prioritizes surveying public corporate career portals rather than attempting to bypass website defensive measures.

The project strictly uses a maximum of two data sources.

---

## 9. Data Requirements

Project data fields are classified as required or optional according to `docs/data_schema_v1.md`, which is the authoritative field-level specification.

Required fields must satisfy the retention and validation rules defined in the schema for a job posting to be accepted into the project dataset. Optional fields may be missing without automatically invalidating the entire record, subject to the schema and cleaning rules.

Raw and original source data must be preserved according to the schema. Normalized and derived fields must be stored separately and must not overwrite original raw data.

---

## 10. Expected Data Scale

Initial targets:

- Approximately 1,000–2,500 valid, deduplicated Data/AI postings;
- Collection duration of approximately 8–10 weeks.

These serve as directional guidelines, not rigid constraints.

Data quality, provenance, and auditability take precedence over raw volume.

---

## 11. Job Title Principles

Must simultaneously store:

- `raw_job_title`;
- `normalized_job_title`.

Only superficial and formatting variations may be normalized.

Do not arbitrarily merge differently named jobs into a common occupational category based on subjective assumptions.

The occupational structure will be investigated downstream via skills and clustering algorithms.

---

## 12. Mandatory Scope

The following components are strictly required:

- Data source evaluation and selection;
- Custom-built data collection / crawler pipeline;
- Provenance and lineage tracking;
- Relevance filtering for job postings;
- Data cleaning;
- Data normalization;
- Job title normalization;
- Duplicate and near-duplicate record detection;
- Skill taxonomy construction;
- Skill extraction;
- Construction of an independent, manually annotated test set;
- Evaluation using Precision, Recall, and F1-score;
- Descriptive market analysis;
- Skill frequency analysis;
- Skill co-occurrence analysis;
- Intra-title similarity analysis;
- Inter-title similarity analysis;
- K-Means as the baseline clustering algorithm;
- Hierarchical clustering for comparison;
- Cluster validation and quality evaluation;
- PCA for dimensional reduction and visualization;
- Analysis of cluster-to-title alignment;
- Explicit documentation of limitations.

---

## 13. Optional Scope

To be undertaken only after all mandatory requirements are fully completed.

Priority order:

1. LLM-based skill extraction comparison on the same benchmark test set.
2. Shallow Decision Tree to interpret discovered clusters.
3. Interactive visualization dashboard/interface.

Optional features must never delay mandatory milestones.

---

## 14. Out of Scope

The project does NOT aim to:

- Establish an official occupational taxonomy for Vietnam;
- Perform a complete, exhaustive census of all Data/AI employment in Vietnam;
- Forecast long-term labor market trends;
- Build a state-of-the-art (SOTA) skill extraction system;
- Fine-tune Large Language Models (LLMs);
- Build RAG systems or autonomous AI Agents;
- Mandate salary prediction modeling;
- Scrape entire job portal websites indiscriminately;
- Bypass CAPTCHAs, authentication barriers, or anti-bot defenses.

---

## 15. Data Publishing Principles

Raw data and verbatim job descriptions may only be stored or published within boundaries permitted by source platform terms.

The code repository prioritizes publishing:

- Source code;
- Data schemas;
- Cleaning rules;
- Skill taxonomy;
- Derived datasets where permissible;
- Aggregate statistical summaries;
- Charts, visualizations, and analytical findings.

Do not by default publish full HTML payloads or verbatim job descriptions to public GitHub repositories.

---

## 16. Known Research Limitations

Findings are representative only of:

- The selected platforms;
- Postings identified by the team as Data/AI;
- The specified observation window;
- Information publicly disclosed by employers.

The dataset is not a nationwide labor census of Vietnam.

Anticipated limitations include:

- Missing or incomplete fields in certain vacancy postings;
- Re-posted or syndicated vacancies;
- Inconsistent title nomenclature across firms;
- Subjectivity in the title normalization process;
- False positives and false negatives in skill extraction;
- Rare / long-tail titles lacking sufficient sample size for robust similarity analysis;
- Clustering reflects data patterns, not an authoritative occupational taxonomy;
- Short observation window precludes long-term macro trend conclusions;
- Salary data is sparse and prone to selection bias.

---

## 17. Criteria for Core Project Completion

The core project is deemed complete when:

- A clean, self-collected dataset is established;
- Data provenance and lineage are fully auditable for every record;
- The skill extractor is formally evaluated on a held-out test set;
- RQ1, RQ2, and RQ3 are thoroughly answered;
- Clustering is executed and evaluated for RQ4;
- Clusters are systematically compared against job titles;
- All conclusions are accompanied by appropriate caveats and limitations;
- The entire pipeline is reproducible end-to-end, from raw input ingestion to analytical results.
