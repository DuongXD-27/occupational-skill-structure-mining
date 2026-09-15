# Skill Annotation Guideline v0.1

**Project:** Vietnam Data & AI Job Skill Landscape 2026  
**Vietnamese title:** Khám phá cấu trúc nghề nghiệp và nhu cầu kỹ năng Data/AI tại Việt Nam năm 2026 từ dữ liệu tuyển dụng trực tuyến tự thu thập  
**Version:** v0.1  
**Annotation date:** 2026-09-15  
**Status:** Pilot / draft for supervisor review

---

## 1. Mục đích

Tài liệu này định nghĩa **cái gì được tính là kỹ năng kỹ thuật (technical skill)** trong dự án và cách chuẩn hóa các cách viết khác nhau về cùng một kỹ năng.

Mục tiêu của guideline là giúp việc gán nhãn có tính:

- **Nhất quán:** cùng một trường hợp được xử lý giống nhau giữa các JD.
- **Tái lập:** người khác có thể đọc guideline và đưa ra quyết định gần giống.
- **Giải thích được:** mỗi skill được giữ hoặc loại theo một rule rõ ràng.
- **Phù hợp với RQ2–RQ4:** tạo representation theo skill mà không áp đặt trước occupational taxonomy.

> **Lưu ý quan trọng:** `skill_group` trong taxonomy chỉ là nhóm tổ chức từ vựng để quản lý taxonomy. Nó **không phải occupational taxonomy** và không được dùng để ép job postings vào các nghề định sẵn trước khi clustering.

---

## 2. Pilot sample dùng để xây v0.1

Từ **51 link** được cung cấp, pilot này sử dụng **48 JD hợp lệ và duy nhất**:

- **ITviec:** 43 JD
- **CareerViet:** 5 JD
- **Loại #14:** trang nhà tuyển dụng OCB, không phải một JD cụ thể.
- **Loại #18:** trang search/listing của ITviec, không phải canonical URL của một JD cụ thể.
- **#48:** trùng hoàn toàn với #47, nên chỉ tính một lần.

Kết quả pilot tạo ra **327 canonical skills**. Trong đó **191 skill chỉ xuất hiện ở 1 JD** và **244 skill xuất hiện tối đa 2 JD**. Long tail lớn là bình thường ở bản bottom-up đầu tiên; chưa dùng ngưỡng tần suất để xóa skill ở v0.1.

### Cách hiểu `observed_count`

`observed_count` trong `skills_taxonomy_v0.1.csv` là **document frequency**:

> số JD duy nhất trong pilot có nhắc rõ skill đó ít nhất một lần.

Một skill xuất hiện 5 lần trong cùng một JD vẫn chỉ cộng **1**. Alias được map về cùng canonical skill trước khi đếm.

**Không được diễn giải `observed_count` của pilot này thành tỷ lệ nhu cầu của toàn thị trường Việt Nam**, vì đây là mẫu induction ban đầu và nguồn đang lệch mạnh về ITviec.

---

## 3. Định nghĩa “technical skill”

Trong dự án này, một **technical skill** là:

> **Một năng lực, phương pháp, công cụ, ngôn ngữ, framework/library, nền tảng, hệ thống dữ liệu, kỹ thuật phân tích hoặc miền kỹ thuật có thể học được và được JD nhắc rõ như một phần của việc thực hiện công việc Data/AI.**

Một item không nhất thiết phải là software/tool mới được tính là skill. Các phương pháp như `Machine Learning`, `ETL`, `Data Modeling`, `A/B Testing`, `Feature Engineering`, `RAG` hoặc `MLOps` vẫn được giữ nếu được nhắc trong ngữ cảnh chuyên môn.

---

## 4. Quyết định scope v0.1

| Loại thông tin | Quyết định | Ví dụ |
|---|---|---|
| Programming/query languages | **INCLUDE** | Python, SQL, Java, C++, R |
| Frameworks/libraries | **INCLUDE** | PyTorch, TensorFlow, Pandas, scikit-learn, LangChain |
| Databases/data platforms | **INCLUDE** | PostgreSQL, MongoDB, BigQuery, Databricks |
| Cloud platforms/services | **INCLUDE** | AWS, Azure, GCP, S3, SageMaker, Vertex AI |
| DevOps/MLOps tooling | **INCLUDE** | Docker, Kubernetes, MLflow, Kubeflow, CI/CD |
| High-level technical methods | **INCLUDE nếu đủ cụ thể và operational** | Machine Learning, NLP, Computer Vision, ETL, Data Modeling, MLOps |
| Statistical/analytical methods | **INCLUDE** | A/B Testing, Regression, Forecasting, Hypothesis Testing |
| Technical data/AI architectures | **INCLUDE** | Data Lakehouse, RAG, Event-Driven Architecture, Multi-Agent Systems |
| Data formats khi được yêu cầu chuyên môn | **INCLUDE** | JSON, Parquet, XML |
| Soft skills | **EXCLUDE** | communication, teamwork, leadership, problem solving |
| Personality traits | **EXCLUDE** | proactive, hard-working, ownership, curiosity |
| Human languages | **EXCLUDE khỏi technical taxonomy** | English, Japanese |
| Education/certification requirement alone | **EXCLUDE** | Bachelor's degree, TOEIC; một chứng chỉ chỉ được giữ nếu tên công nghệ bên trong cũng là skill độc lập |
| Years of experience/seniority | **EXCLUDE** | 3+ years, Senior, Lead |
| Job/occupation labels | **EXCLUDE** | Data Engineer, Data Scientist, AI Engineer |
| Generic umbrella labels quá rộng | **EXCLUDE mặc định** | AI, Technology, Data |
| Company/product marketing text | **EXCLUDE** nếu không phải requirement/responsibility của role | công nghệ chỉ được mô tả như sản phẩm/culture của công ty |

### Phân biệt role label và competency

- `Data Engineer` trong title → **không phải skill**.
- `Data Engineering` chỉ như tên nghề/chuyên môn → **không tự động annotate**.
- `Data Analysis` trong câu “perform data analysis / strong data analysis skills” → **có thể annotate**, vì đây là năng lực cụ thể.
- `AI` đứng một mình → quá rộng, **không đưa vào taxonomy v0.1**.
- `Generative AI`, `Machine Learning`, `Computer Vision`, `NLP` → đủ cụ thể để giữ.

---

## 5. Vùng văn bản được dùng để annotate

### INCLUDE

Ưu tiên đọc các vùng:

1. `Requirements / Yêu cầu công việc`
2. `Responsibilities / Mô tả công việc`
3. `Nice to have / Preferred`
4. Employer-provided `Kỹ năng`/skill tags của chính vacancy
5. Title **chỉ khi title chứa technology/skill cụ thể**, ví dụ `Data Engineer (Python, Kafka)`.

### EXCLUDE

Không lấy skill chỉ vì nó xuất hiện trong:

- mô tả chung về công ty;
- phúc lợi;
- văn hóa/công cụ được quảng bá nhưng không liên quan trực tiếp tới role;
- danh sách việc làm tương tự;
- navigation/footer;
- tên nghề tự thân.

Nếu một công nghệ xuất hiện ở phần marketing **và** đồng thời là requirement/responsibility của role, vẫn annotate dựa trên phần role.

---

## 6. Required và Nice-to-have

Ở v0.1, **cả required và preferred/nice-to-have đều được tính**, vì mục tiêu hiện tại là **taxonomy induction**: khám phá vocabulary kỹ năng mà thị trường sử dụng.

Tuy nhiên, khi bước sang demand analysis chính thức, nên lưu thêm trường như:

- `requirement_level = required`
- `requirement_level = preferred`
- `requirement_level = responsibility/context`

để không đánh đồng mức độ bắt buộc.

---

## 7. Abbreviation rules

### 7.1. Abbreviation chuẩn, không mơ hồ

Map về một canonical skill:

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
- `ETL` và `ELT` là **hai skill khác nhau**, không merge.

### 7.2. Abbreviation mơ hồ: chỉ map khi context đủ rõ

Ví dụ `CV` có thể là:

- `Computer Vision`, hoặc
- curriculum vitae.

Chỉ map `CV` → `Computer Vision` khi ngữ cảnh kỹ thuật xác nhận, ví dụ đi cùng `OpenCV`, image/video models, object detection, hoặc câu nói rõ Computer Vision.

### 7.3. Không suy diễn acronym không xuất hiện

Nếu JD chỉ viết `Retrieval-Augmented Generation`, canonicalize về RAG concept. Nhưng nếu JD không nhắc concept đó thì không suy ra từ việc job dùng LLM.

---

## 8. Synonym và spelling normalization

Các biến thể chỉ khác case, space, hyphen hoặc tên phổ biến được map về cùng canonical item.

Ví dụ:

- `Postgres`, `Postgre SQL` → `PostgreSQL`
- `PowerBI` → `Power BI`
- `sklearn`, `scikit learn` → `scikit-learn`
- `MS SQL Server`, `MSSQL` → `Microsoft SQL Server`
- `K8s` → `Kubernetes`
- `GenAI` → `Generative AI`

Không merge hai công nghệ chỉ vì chúng thường đi cùng nhau.

Ví dụ:

- `PyTorch` ≠ `TensorFlow`
- `AWS` ≠ `Azure`
- `Data Lake` ≠ `Data Warehouse`
- `RAG` ≠ `Vector Database`
- `ETL` ≠ `ELT`

---

## 9. Parent–child technology rule

Không tự động suy diễn parent hoặc child skill.

Ví dụ:

- JD chỉ viết `SageMaker` → annotate `Amazon SageMaker`; **không tự động thêm AWS**.
- JD viết `AWS SageMaker` → cả `Amazon Web Services` và `Amazon SageMaker` đều được coi là explicit.
- JD viết `Kubernetes` → không suy ra `Docker`.
- JD viết `LangChain` → không suy ra `RAG`.
- JD viết `LLM` → không suy ra `Prompt Engineering`.

Lý do: project cần đo **những gì nhà tuyển dụng thực sự viết**, không đo kiến thức mà annotator cho rằng “đương nhiên phải biết”.

---

## 10. Implicit skill rule

**Mặc định: KHÔNG annotate implicit skills ở v0.1.**

Ví dụ:

- “Build dashboards” → annotate `Dashboarding`; **không suy ra Power BI/Tableau**.
- “Deploy models to production” → có thể annotate `Model Deployment`; **không suy ra Docker/Kubernetes/AWS**.
- “Build recommendation systems” → annotate `Recommendation Systems`; **không suy ra Python/PyTorch**.
- “Work with relational databases” → annotate `Relational Databases`; **không suy ra PostgreSQL/MySQL**.

Rule-based extractor và gold annotation phải bám vào evidence hiển thị trong text.

---

## 11. Composite mentions và alternatives

Nếu JD liệt kê nhiều công nghệ rõ ràng bằng `/`, `or`, `and`, mỗi technology được annotate riêng.

Ví dụ:

- `C/C++` → `C` + `C++`
- `PyTorch/TensorFlow` → `PyTorch` + `TensorFlow`
- `AWS/GCP/Azure` → ba cloud skills
- `Airflow, Dagster or Prefect` → ba skills

Điều này áp dụng kể cả khi JD nói “one of”.

---

## 12. Context-dependent cases

### 12.1. Applied business/analytics skills

Các use case được giữ **khi role yêu cầu người làm phải xây dựng/phân tích chúng như một năng lực kỹ thuật**, ví dụ:

- Fraud Detection
- Risk Scoring
- Credit Scoring
- Customer Analytics
- Cohort Analysis
- Dynamic Pricing

Không giữ nếu cụm từ chỉ mô tả ngành kinh doanh hoặc mục tiêu business chung.

### 12.2. Data governance / quality / security

Giữ khi JD yêu cầu thực hiện hoặc thiết kế:

- Data Governance
- Data Quality
- Data Validation
- Data Security
- Data Lineage

Không giữ các từ pháp lý/compliance chung nếu không thể hiện một nhiệm vụ kỹ thuật cụ thể.

### 12.3. Cloud

- `AWS`, `Azure`, `GCP` → giữ.
- `cloud` → chỉ giữ dưới canonical `Cloud Computing` khi JD yêu cầu kiến thức/kinh nghiệm cloud.
- “cloud company / cloud product” trong mô tả doanh nghiệp → không giữ.

### 12.4. Generic software practices

Các capability kỹ thuật rõ ràng như `API Design`, `Microservices`, `CI/CD`, `Observability`, `Debugging` được giữ.

Soft/management practices như stakeholder management, mentoring, communication, ownership không nằm trong taxonomy technical v0.1.

---

## 13. Counting rule

Đối với mỗi JD:

1. Normalize raw mention → canonical skill.
2. Deduplicate trong cùng JD.
3. Mỗi canonical skill có giá trị 0/1 cho JD đó.
4. `observed_count` = tổng số JD có giá trị 1.
5. Exact duplicate postings chỉ tính một lần.

Ví dụ nếu một JD nhắc `Python` 8 lần:

```text
Python document count = 1
```

Nếu ba JD lần lượt viết `Postgres`, `PostgreSQL`, `Postgre SQL`:

```text
canonical = PostgreSQL
observed_count = 3
```

---

## 14. Skill groups v0.1

Các group trong CSV dùng để quản lý vocabulary:

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

**Không sử dụng các group này làm occupational labels trong RQ4.** Clustering nghề vẫn phải dựa trên representation của skill ở cấp job posting.

---

## 15. Sanity check từ pilot

Top 10 canonical skills theo `observed_count` của 48-JD pilot:

| Rank | Canonical skill | JD count |
|---:|---|---:|
| 1 | Python | 33 |
| 2 | SQL | 26 |
| 3 | Machine Learning | 18 |
| 4 | ETL | 16 |
| 5 | Large Language Models | 15 |
| 6 | Apache Spark | 13 |
| 7 | Amazon Web Services | 13 |
| 8 | ELT | 11 |
| 9 | Data Warehouse | 11 |
| 10 | Apache Airflow | 9 |

Bảng này chỉ là **sanity check của taxonomy pilot**, chưa phải kết quả RQ2 chính thức.

---

## 16. Quy trình annotation đề xuất cho các batch tiếp theo

1. Đọc JD và highlight raw technical mentions.
2. Áp dụng include/exclude rules trước khi nhìn taxonomy.
3. Nếu concept đã có trong taxonomy → map về `canonical_name`.
4. Nếu concept mới và hợp lệ → thêm canonical skill mới, append `skill_id` mới.
5. Ghi alias mới nếu chỉ là biến thể của skill cũ.
6. Không thêm implicit skill.
7. Mỗi JD deduplicate trước khi cộng count.
8. Flag trường hợp không chắc chắn để review thay vì tự đoán.
9. Định kỳ review các singleton/rare skills để phát hiện:
   - typo;
   - alias chưa merge;
   - item quá chi tiết;
   - business phrase bị nhầm thành technical skill.

---

## 17. Các quyết định nên review ở v0.2

Sau khi annotate thêm dữ liệu, cần xem lại:

- có giữ tất cả data formats (`CSV`, `XML`, `JSON`) như skill riêng không;
- có tách platform và service ở nhiều level không;
- có giữ các applied use cases tần suất thấp không;
- có tạo hierarchy chính thức `parent_skill_id` không;
- có thêm `requirement_level` và `evidence_span` không;
- có cần minimum document frequency cho downstream modeling không.

**Không nên xóa singleton chỉ vì hiếm ở bước induction.** Việc pruning nên xảy ra sau khi đã kiểm tra liệu singleton là skill thật, alias hay noise.

---

## 18. Quan hệ với LLM comparator

Nếu thực hiện optional LLM experiment, cả rule-based extractor và LLM phải được đánh giá trên **cùng held-out set, cùng guideline và cùng canonical taxonomy**.

LLM không được nhận credit chỉ vì trả về một concept nằm ngoài scope. Prediction phải normalize về taxonomy trước khi tính Precision / Recall / F1.

Điều này giúp câu hỏi so sánh thực sự là:

> Với **cùng một định nghĩa skill và cùng corpus**, LLM cải thiện extraction quality bao nhiêu so với Dictionary + Regex + Fuzzy, và đổi lại phải trả giá gì về cost, dependency, reproducibility và interpretability?

---

## 19. Versioning

- `v0.1`: bottom-up taxonomy từ 48 unique usable JDs của pilot.
- Khi bổ sung skill mới, **không tái sử dụng `skill_id` cũ cho concept khác**.
- Alias có thể mở rộng nhưng canonical name chỉ đổi khi có lý do rõ ràng và phải ghi migration.
- Trước khi dùng cho analysis chính thức, nên freeze một version (ví dụ `v1.0`) và lưu changelog.

