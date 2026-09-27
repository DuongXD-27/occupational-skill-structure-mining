# Hướng dẫn Gán nhãn Kỹ năng (Skill Annotation Guideline)

**Dự án:** Vietnam Data & AI Job Skill Landscape 2026  
**Tên tiếng Việt:** Khám phá cấu trúc nghề nghiệp và nhu cầu kỹ năng Data/AI tại Việt Nam năm 2026 từ dữ liệu tuyển dụng trực tuyến tự thu thập  
**Phiên bản:** v0.1  
**Ngày gán nhãn:** 2026-09-15  
**Trạng thái:** Bản thử nghiệm (Pilot) phục vụ đánh giá chuyên môn  

---

## 1. Mục đích

Tài liệu này định nghĩa **những gì được coi là một kỹ năng kỹ thuật (technical skill)** trong dự án và cách chuẩn hóa các dạng thể hiện bề mặt khác nhau trỏ về cùng một kỹ năng.

Hướng dẫn này nhằm đảm bảo quá trình gán nhãn đạt được các tiêu chuẩn:

- **Tính nhất quán (Consistent):** các trường hợp cùng loại phải được xử lý giống nhau trên toàn bộ các mô tả công việc (JDs).
- **Tính tái lập (Reproducible):** người gán nhãn khác khi đọc hướng dẫn này cũng có thể đưa ra các quyết định tương tự.
- **Tính diễn giải (Interpretable):** mỗi kỹ năng được giữ lại hoặc loại bỏ đều phải dựa trên một quy tắc rõ ràng.
- **Bám sát RQ2–RQ4:** tạo ra biểu diễn dựa trên kỹ năng mà không áp đặt định kiến về một taxonomy nghề nghiệp định sẵn.

> **Lưu ý quan trọng:** `skill_group` trong taxonomy chỉ là danh mục phân loại phục vụ quản lý từ vựng. Đây **không phải là taxonomy nghề nghiệp** và tuyệt đối không được dùng để gượng ép các tin tuyển dụng vào các nghề nghiệp định sẵn trước khi phân cụm.

---

## 2. Mẫu dữ liệu chính thức được sử dụng để đếm tần suất

Tập mẫu chuẩn làm căn cứ là `data/sample/sample_jobs.jsonl`, bao gồm **45 mô tả công việc duy nhất**, 100% từ **ITviec**. Đây là tập mẫu ground-truth được chuẩn bị trong PR #3 và là ngữ cảnh duy nhất được dùng để tính toán `observed_count` trong [taxonomy/skills_taxonomy.csv](taxonomy/skills_taxonomy.csv).

Các bản ghi CareerViet không thuộc tập mẫu này. Phạm vi nguồn được phê duyệt chỉ định ITviec làm nguồn chính và TopCV là nguồn dự phòng.

Taxonomy bao gồm **246 kỹ năng chuẩn hóa (canonical skills)**, và mọi kỹ năng được giữ lại đều xuất hiện trong ít nhất một tin tuyển dụng thuộc tập 45 tin chính thức. Trong đó, **102 kỹ năng xuất hiện đúng 1 lần**, và **150 kỹ năng xuất hiện tối đa 2 lần**. Các kỹ năng có `observed_count` bằng 0 đều bị loại bỏ vì không có bằng chứng từ tập dữ liệu mẫu chính thức.

### Diễn giải về chỉ số `observed_count`

`observed_count` trong [taxonomy/skills_taxonomy.csv](taxonomy/skills_taxonomy.csv) thể hiện **tần suất tài liệu (Document Frequency)**:

> số lượng tin tuyển dụng duy nhất trong tập mẫu 45 tin ITviec chính thức có đề cập tường minh đến kỹ năng đó ít nhất một lần.

Nếu một kỹ năng xuất hiện 5 lần trong cùng một tin tuyển dụng, kỹ năng đó vẫn chỉ đóng góp **1** vào số lần quan sát. Tên chuẩn (canonical name), từ viết tắt (abbreviation) và từ đồng nghĩa (aliases) đều được ánh xạ về cùng một kỹ năng chuẩn trước khi tính toán.

**Các giá trị `observed_count` này không được hiểu là tỷ lệ nhu cầu trên toàn thị trường Việt Nam**, vì đây là tập mẫu nhỏ phục vụ xác thực taxonomy từ một nguồn đơn lẻ.

---

## 3. Định nghĩa về "Kỹ năng Kỹ thuật" (Technical Skill)

Trong dự án này, một **kỹ năng kỹ thuật** là:

> **Một năng lực có thể học tập được, một phương pháp, công cụ, ngôn ngữ, thư viện/framework, nền tảng, hệ thống dữ liệu, kỹ thuật phân tích, hoặc miền kỹ thuật được đề cập rõ ràng trong tin tuyển dụng như một phần của công việc Data/AI.**

Một mục không nhất thiết phải là một sản phẩm phần mềm hay công cụ mới được tính là kỹ năng. Các phương pháp kỹ thuật như `Machine Learning`, `ETL`, `Data Modeling`, `A/B Testing`, `Feature Engineering`, `RAG`, hoặc `MLOps` cũng được giữ lại khi chúng được đề cập trong ngữ cảnh chuyên môn/kỹ thuật.

---

## 4. Quyết định phạm vi (Scope Decisions)

| Loại thông tin | Quyết định | Ví dụ minh họa |
|---|---|---|
| Ngôn ngữ lập trình / truy vấn | **GIỮ LẠI (INCLUDE)** | Python, SQL, Java, C++, R |
| Thư viện / Framework | **GIỮ LẠI (INCLUDE)** | PyTorch, TensorFlow, Pandas, scikit-learn, LangChain |
| Cơ sở dữ liệu / Nền tảng dữ liệu | **GIỮ LẠI (INCLUDE)** | PostgreSQL, MongoDB, BigQuery, Databricks |
| Nền tảng / Dịch vụ đám mây (Cloud) | **GIỮ LẠI (INCLUDE)** | AWS, Azure, GCP, S3, SageMaker, Vertex AI |
| Công cụ DevOps / MLOps | **GIỮ LẠI (INCLUDE)** | Docker, Kubernetes, MLflow, Kubeflow, CI/CD |
| Phương pháp kỹ thuật cấp cao | **GIỮ LẠI nếu đủ cụ thể và mang tính tác vụ** | Machine Learning, NLP, Computer Vision, ETL, Data Modeling, MLOps |
| Phương pháp thống kê / phân tích | **GIỮ LẠI (INCLUDE)** | A/B Testing, Regression, Forecasting, Hypothesis Testing |
| Kiến trúc dữ liệu / AI kỹ thuật | **GIỮ LẠI (INCLUDE)** | Data Lakehouse, RAG, Event-Driven Architecture, Multi-Agent Systems |
| Định dạng dữ liệu mang tính kỹ thuật | **GIỮ LẠI (INCLUDE)** | JSON, Parquet, XML |
| Kỹ năng mềm (Soft skills) | **LOẠI TRỪ (EXCLUDE)** | communication, teamwork, leadership, problem solving |
| Phẩm chất / Tính cách cá nhân | **LOẠI TRỪ (EXCLUDE)** | proactive, hard-working, ownership, curiosity |
| Ngôn ngữ tự nhiên | **LOẠI TRỪ khỏi taxonomy kỹ thuật** | Tiếng Anh (English), Tiếng Nhật (Japanese) |
| Yêu cầu bằng cấp / chứng chỉ đơn thuần | **LOẠI TRỪ (EXCLUDE)** | Bachelor's degree, TOEIC; chứng chỉ chỉ được giữ lại nếu công nghệ nêu trong chứng chỉ đó là một kỹ năng độc lập |
| Số năm kinh nghiệm / Cấp bậc | **LOẠI TRỪ (EXCLUDE)** | 3+ years, Senior, Lead |
| Nhãn chức danh / Nghề nghiệp | **LOẠI TRỪ (EXCLUDE)** | Data Engineer, Data Scientist, AI Engineer |
| Thuật ngữ chung chung quá rộng | **MẶC ĐỊNH LOẠI TRỪ** | AI, Technology, Data |
| Văn bản marketing của công ty | **LOẠI TRỪ** trừ khi đó là yêu cầu/trách nhiệm của vai trò | công nghệ chỉ được nhắc đến như sản phẩm công ty làm hoặc văn hóa chung |

### Phân biệt Nhãn vai trò với Năng lực chuyên môn

- `Data Engineer` nằm trong chức danh công việc → **không phải là kỹ năng**.
- `Data Engineering` chỉ dùng làm nhãn định danh nghề nghiệp/chuyên môn → **không tự động gán nhãn**.
- `Data Analysis` trong ngữ cảnh như "perform data analysis" hoặc "strong data analysis skills" → **được gán nhãn**, vì nó mô tả năng lực công việc cụ thể.
- `AI` đứng độc lập một mình → quá rộng, **không đưa vào taxonomy**.
- `Generative AI`, `Machine Learning`, `Computer Vision`, `NLP` → đủ mức độ cụ thể để giữ lại.

---

## 5. Vùng văn bản được sử dụng để gán nhãn

### ĐƯỢC LẤY (INCLUDE)

Ưu tiên các phần sau:

1. `Requirements` (Yêu cầu công việc)
2. `Responsibilities` (Trách nhiệm công việc)
3. `Nice to have / Preferred` (Kỹ năng ưu tiên/điểm cộng)
4. Các thẻ `Skills` do nhà tuyển dụng cung cấp trực tiếp cho vị trí đó
5. Chức danh công việc **chỉ khi chức danh có chứa rõ ràng công nghệ/kỹ năng**, ví dụ: `Data Engineer (Python, Kafka)`.

### LOẠI TRỪ (EXCLUDE)

Không ghi nhận kỹ năng nếu nó chỉ xuất hiện trong:

- phần mô tả chung về công ty;
- chế độ đãi ngộ, phúc lợi;
- văn hóa công ty hoặc các công cụ quảng bá không liên quan đến vị trí tuyển dụng;
- danh sách việc làm tương tự;
- nội dung điều hướng, chân trang (footer);
- chính tiêu đề nhãn nghề nghiệp.

Nếu một công nghệ vừa xuất hiện trong phần giới thiệu công ty vừa được nêu rõ là yêu cầu/trách nhiệm của vai trò, hãy gán nhãn dựa trên bằng chứng ở phần vai trò cụ thể.

---

## 6. Kỹ năng bắt buộc so với Kỹ năng ưu tiên

Trong phiên bản v0.1, **cả kỹ năng bắt buộc và kỹ năng ưu tiên (nice-to-have) đều được tính**, vì mục tiêu hiện tại là **xây dựng từ vựng taxonomy**: khám phá toàn bộ vốn từ vựng kỹ năng mà thị trường đang sử dụng.

Tuy nhiên, đối với phân tích nhu cầu chính thức ở các giai đoạn sau, cần lưu trữ thêm các trường phân cấp:

- `requirement_level = required`
- `requirement_level = preferred`
- `requirement_level = responsibility/context`

Điều này giúp ngăn chặn việc đánh đồng giữa kỹ năng bắt buộc và kỹ năng tự chọn.

---

## 7. Quy tắc xử lý từ viết tắt (Abbreviations)

File CSV của taxonomy sử dụng cấu trúc:

```text
skill_id,canonical_name,abbreviation,aliases,skill_group,observed_count
```

`abbreviation` lưu các dạng viết tắt tiêu chuẩn của tên chuẩn. `aliases` lưu các biến thể về chính tả, cách viết, dấu cách hoặc tên gọi khác; từ viết tắt không được lặp lại trong `aliases`. Nhiều giá trị trong các trường này được phân tách bằng dấu chấm phẩy `; `.

Ví dụ:

```text
canonical_name = Natural Language Processing
abbreviation = NLP
aliases = text processing; xử lý ngôn ngữ tự nhiên
```

### 7.1. Các từ viết tắt tiêu chuẩn, không mơ hồ

Ánh xạ trực tiếp về kỹ năng chuẩn:

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
- `ETL` và `ELT` là **hai kỹ năng kỹ thuật khác nhau**, tuyệt đối không được gộp làm một.

### 7.2. Từ viết tắt mơ hồ: Chỉ ánh xạ khi có đủ ngữ cảnh

Ví dụ, `CV` có thể mang nghĩa:

- `Computer Vision` (Thị giác máy tính), hoặc
- curriculum vitae (hồ sơ xin việc).

Chỉ ánh xạ `CV` → `Computer Vision` khi ngữ cảnh kỹ thuật xác nhận rõ ý nghĩa, ví dụ khi nó đi kèm với `OpenCV`, mô hình hình ảnh/video, nhận diện vật thể (object detection), hoặc có nhắc đến Computer Vision.

### 7.3. Không suy diễn các từ viết tắt hoặc khái niệm không được đề cập

Nếu tin tuyển dụng ghi `Retrieval-Augmented Generation`, hãy chuẩn hóa về khái niệm RAG. Tuy nhiên, nếu tin tuyển dụng không đề cập khái niệm đó, không được tự ý suy ra RAG chỉ vì vị trí đó có làm việc với LLMs.

---

## 8. Chuẩn hóa từ đồng nghĩa và biến thể chính tả

Các biến thể chỉ khác nhau về viết hoa/viết thường, dấu cách, dấu gạch nối, hoặc quy ước đặt tên thông dụng phải được ánh xạ về cùng một tên chuẩn.

Ví dụ:

- `Postgres`, `Postgre SQL` → `PostgreSQL`
- `PowerBI` → `Power BI`
- `sklearn`, `scikit learn` → `scikit-learn`
- `MS SQL Server`, `MSSQL` → `Microsoft SQL Server`
- `K8s` → `Kubernetes`
- `GenAI` → `Generative AI`

Tuyệt đối không gộp hai công nghệ riêng biệt chỉ vì chúng thường xuyên đồng xuất hiện cùng nhau.

Ví dụ:

- `PyTorch` ≠ `TensorFlow`
- `AWS` ≠ `Azure`
- `Data Lake` ≠ `Data Warehouse`
- `RAG` ≠ `Vector Database`
- `ETL` ≠ `ELT`

---

## 9. Quy tắc Công nghệ Cha – Con (Parent–Child)

Không tự động suy luận kỹ năng cha từ kỹ năng con hoặc ngược lại.

Ví dụ:

- Tin tuyển dụng chỉ đề cập `SageMaker` → gán nhãn `Amazon SageMaker`; **không tự ý bổ sung AWS**.
- Tin tuyển dụng ghi rõ `AWS SageMaker` → cả `Amazon Web Services` và `Amazon SageMaker` đều được ghi nhận tường minh.
- Tin tuyển dụng đề cập `Kubernetes` → không tự ý suy ra `Docker`.
- Tin tuyển dụng đề cập `LangChain` → không tự ý suy ra `RAG`.
- Tin tuyển dụng đề cập `LLM` → không tự ý suy ra `Prompt Engineering`.

Lý do: dự án hướng tới đo lường **chính xác những gì nhà tuyển dụng thực sự viết ra**, không phải những gì người gán nhãn cho là ứng viên "hiển nhiên cần phải biết".

---

## 10. Quy tắc Kỹ năng Ngầm (Implicit Skills)

**Quy tắc mặc định: TUYỆT ĐỐI KHÔNG gán nhãn kỹ năng ngầm trong phiên bản v0.1.**

Ví dụ:

- "Xây dựng dashboard" → gán nhãn `Dashboarding`; **không tự ý suy ra Power BI hoặc Tableau**.
- "Deploy models to production" → có thể gán nhãn `Model Deployment`; **không tự ý suy ra Docker/Kubernetes/AWS**.
- "Build recommendation systems" → gán nhãn `Recommendation Systems`; **không tự ý suy ra Python/PyTorch**.
- "Làm việc với cơ sở dữ liệu quan hệ" → gán nhãn `Relational Databases`; **không tự ý suy ra PostgreSQL/MySQL**.

Bộ trích xuất dựa trên quy tắc và tập nhãn vàng chuẩn (gold annotations) phải dựa hoàn toàn vào bằng chứng xuất hiện thực tế trong văn bản.

---

## 11. Các đề cập kết hợp và lựa chọn thay thế

Nếu tin tuyển dụng liệt kê nhiều công nghệ bằng dấu gạch chéo `/`, chữ `hoặc (or)`, hoặc `và (and)`, hãy gán nhãn riêng cho từng công nghệ.

Ví dụ:

- `C/C++` → `C` + `C++`
- `PyTorch/TensorFlow` → `PyTorch` + `TensorFlow`
- `AWS/GCP/Azure` → ghi nhận ba kỹ năng đám mây riêng biệt
- `Airflow, Dagster or Prefect` → ba kỹ năng riêng biệt

Điều này áp dụng ngay cả khi tin tuyển dụng ghi là "chỉ cần một trong các công nghệ sau".

---

## 12. Các trường hợp phụ thuộc ngữ cảnh

### 12.1. Kỹ năng phân tích / nghiệp vụ ứng dụng

Các bài toán ứng dụng được giữ lại **khi vai trò đòi hỏi nhân sự phải xây dựng, lập mô hình hoặc phân tích chúng như một năng lực kỹ thuật**, ví dụ:

- Fraud Detection (Phát hiện gian lận)
- Risk Scoring (Chấm điểm rủi ro)
- Credit Scoring (Chấm điểm tín dụng)
- Customer Analytics (Phân tích khách hàng)
- Cohort Analysis (Phân tích đoàn hệ)
- Dynamic Pricing (Định giá động)

Không giữ lại nếu cụm từ chỉ đơn thuần mô tả lĩnh vực kinh doanh hoặc mục tiêu kinh doanh chung của công ty.

### 12.2. Quản trị dữ liệu / Chất lượng dữ liệu / Bảo mật

Giữ lại khi tin tuyển dụng yêu cầu nhân sự phải triển khai, thiết kế hoặc thực thi:

- Data Governance (Quản trị dữ liệu)
- Data Quality (Chất lượng dữ liệu)
- Data Validation (Kiểm thực dữ liệu)
- Data Security (Bảo mật dữ liệu)
- Data Lineage (Dòng dữ liệu)

Không giữ lại các thuật ngữ pháp lý/tuân thủ chung chung trừ khi nó đại diện cho một tác vụ kỹ thuật cụ thể.

### 12.3. Điện toán đám mây (Cloud)

- `AWS`, `Azure`, `GCP` → giữ lại tên nền tảng cụ thể.
- `cloud` → chỉ giữ lại dưới tên chuẩn `Cloud Computing` khi tin tuyển dụng đòi hỏi kiến thức/kinh nghiệm về đám mây.
- "công ty cloud / sản phẩm cloud" trong phần giới thiệu công ty → không giữ lại.

### 12.4. Thực hành kỹ thuật phần mềm thông dụng

Các năng lực kỹ thuật rõ ràng như `API Design`, `Microservices`, `CI/CD`, `Observability` và `Debugging` được giữ lại.

Các thực hành kỹ năng mềm/quản lý như quản lý bên liên quan, cố vấn (mentoring), giao tiếp và tinh thần trách nhiệm không thuộc về taxonomy kỹ thuật.

---

## 13. Quy tắc tính toán tần suất (Counting Rule)

Đối với mỗi tin tuyển dụng (JD):

1. Chuẩn hóa dạng thể hiện thô → tên kỹ năng chuẩn (canonical skill).
2. Khử trùng lặp kỹ năng trong phạm vi cùng một JD.
3. Mỗi kỹ năng chuẩn nhận giá trị 0 hoặc 1 đối với JD đó.
4. `observed_count` = tổng số lượng JD có giá trị 1.
5. Các tin tuyển dụng trùng lặp chính xác chỉ được tính 1 lần.

Tần suất được tính toán từ các trường `raw_job_title`, `job_description`, và `job_requirements` trong tập mẫu chính thức. Khi một thuật ngữ ngắn bị bao hàm trong một thuật ngữ taxonomy dài hơn, thuật ngữ dài hơn sẽ được ưu tiên; ví dụ: `BI` bên trong `Power BI` sẽ không được tính độc lập cho `Business Intelligence`. Các từ viết tắt nhạy cảm với ngữ cảnh và các tên ngôn ngữ ngắn được xử lý thận trọng để tránh khớp sai như `CV` (hồ sơ), `R` (trong R&D), hoặc `Go` (trong văn bản tiếng Anh thông thường).

Chạy lệnh `python scripts/recount_taxonomy.py` từ thư mục gốc của repository để tái lập các số liệu tần suất taxonomy và loại bỏ các kỹ năng không quan sát được trong tập mẫu chính thức.

Ví dụ: nếu một JD nhắc đến `Python` 8 lần:

```text
Python document count = 1
```

Nếu ba JD lần lượt sử dụng `Postgres`, `PostgreSQL`, và `Postgre SQL`:

```text
canonical = PostgreSQL
observed_count = 3
```

---

## 14. Các nhóm kỹ năng (Skill Groups)

Các nhóm trong file CSV được dùng để tổ chức vốn từ vựng:

- Programming & Query Languages (Ngôn ngữ lập trình & truy vấn)
- Data Analysis & BI (Phân tích dữ liệu & BI)
- Data Engineering & Architecture (Kỹ nghệ dữ liệu & Kiến trúc)
- Distributed, Streaming & Big Data (Dữ liệu lớn, phân tán & streaming)
- Databases, Storage & Data Formats (Cơ sở dữ liệu, lưu trữ & định dạng)
- Cloud Platforms & Services (Nền tảng & dịch vụ đám mây)
- DevOps, MLOps & Infrastructure (DevOps, MLOps & hạ tầng)
- Machine Learning, Statistics & Optimization (Học máy, thống kê & tối ưu hóa)
- Generative AI & Agentic Systems (AI tạo sinh & hệ thống Agentic)
- NLP, Vision & Multimodal AI (Xử lý ngôn ngữ, thị giác & AI đa phương thức)
- Software Engineering & APIs (Kỹ nghệ phần mềm & APIs)
- Data Quality, Testing & Observability (Chất lượng dữ liệu, kiểm thử & khả năng giám sát)
- Security Engineering (Kỹ thuật bảo mật)
- Applied Analytics & Business Platforms (Phân tích ứng dụng & nền tảng nghiệp vụ)
- Engineering Tools & Collaboration (Công cụ kỹ thuật & cộng tác)

**Không sử dụng các nhóm này làm nhãn nghề nghiệp trong RQ4.** Việc phân cụm nghề nghiệp vẫn phải hoàn toàn dựa trên biểu diễn vector kỹ năng thực tế của từng tin tuyển dụng.

---

## 15. Kiểm tra tính hợp lý ban đầu (Sanity Check)

Top 10 kỹ năng chuẩn hóa có `observed_count` cao nhất trong mẫu 45 tin ITviec chính thức:

| Thứ hạng | Tên kỹ năng chuẩn (Canonical skill) | Số tin tuyển dụng xuất hiện |
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

Bảng này chỉ đóng vai trò **kiểm tra tính hợp lý cho taxonomy thử nghiệm**, không phải là kết quả chính thức cho RQ2.

---

## 16. Quy trình gán nhãn khuyến nghị cho các đợt dữ liệu tiếp theo

1. Đọc tin tuyển dụng (JD) và đánh dấu các đoạn văn bản kỹ thuật thô.
2. Áp dụng quy tắc bao hàm/loại trừ trước khi tra cứu taxonomy.
3. Nếu khái niệm đã tồn tại trong taxonomy → ánh xạ về `canonical_name`.
4. Nếu khái niệm mới và hợp lệ → thêm kỹ năng chuẩn mới và cấp mã `skill_id` mới.
5. Ghi lại alias mới nếu đề cập chỉ là một biến thể của kỹ năng đã có.
6. Không thêm các kỹ năng ngầm suy diễn.
7. Khử trùng lặp kỹ năng trong phạm vi mỗi tin tuyển dụng trước khi tăng bộ đếm.
8. Gắn cờ các trường hợp chưa chắc chắn để hội ý thay vì phỏng đoán.
9. Định kỳ rà soát các kỹ năng đơn lẻ / tần suất hiếm để phát hiện:
   - lỗi chính tả;
   - các alias chưa được gộp;
   - các mục quá chi tiết/rời rạc;
   - các cụm từ nghiệp vụ kinh doanh bị phân loại nhầm thành kỹ năng kỹ thuật.

---

## 17. Các quyết định cần xem xét lại trong phiên bản tiếp theo

Sau khi gán nhãn thêm dữ liệu, cần xem xét lại:

- liệu tất cả các định dạng dữ liệu (`CSV`, `XML`, `JSON`) có nên tiếp tục là các kỹ năng riêng lẻ;
- các nền tảng và dịch vụ có nên được biểu diễn ở nhiều cấp bậc phân cấp hay không;
- các bài toán nghiệp vụ ứng dụng tần suất thấp có nên giữ lại;
- có nên đưa vào cấu trúc phân cấp `parent_skill_id` chính thức;
- có nên bổ sung các trường `requirement_level` và `evidence_span`;
- ngưỡng tần suất tài liệu tối thiểu cho việc huấn luyện mô hình hạ nguồn.

**Không xóa một kỹ năng đơn lẻ chỉ vì nó hiếm trong quá trình xây dựng taxonomy.** Việc tinh lọc chỉ nên diễn ra sau khi kiểm tra xem kỹ năng hiếm đó là một kỹ năng thực thụ, một alias chưa được hợp nhất, hay là nhiễu.

---

## 18. Mối liên hệ với Thử nghiệm So sánh LLM

Nếu thử nghiệm so sánh với LLM tùy chọn được tiến hành, cả bộ trích xuất dựa trên quy tắc (rule-based) và LLM đều phải được đánh giá trên **cùng một tập kiểm thử độc lập (held-out set), sử dụng cùng hướng dẫn gán nhãn và cùng taxonomy chuẩn hóa**.

LLM không được cộng điểm chỉ vì trả về một khái niệm nằm ngoài phạm vi đã định nghĩa. Các dự đoán của LLM phải được chuẩn hóa về taxonomy trước khi tính Precision / Recall / F1.

Điều này đảm bảo phép so sánh thực sự trả lời câu hỏi:

> Với **cùng định nghĩa kỹ năng và cùng ngữ cảnh văn bản**, LLM cải thiện chất lượng trích xuất bao nhiêu so với phương pháp Từ điển + Regex + Fuzzy matching, và sự đánh đổi về chi phí, phụ thuộc hạ tầng, tính tái lập và khả năng diễn giải là gì?

---

## 19. Quản lý phiên bản

- `v0.1`: các số liệu tần suất taxonomy được xác thực trên 45 tin tuyển dụng ITviec duy nhất trong `data/sample/sample_jobs.jsonl`.
- Khi bổ sung kỹ năng mới, **tuyệt đối không tái sử dụng mã `skill_id` đã có cho một khái niệm khác**.
- Danh sách alias có thể mở rộng, nhưng tên chuẩn (canonical names) chỉ nên thay đổi khi có lý do rõ ràng kèm lịch sử chuyển đổi (migration log).
- Trước khi sử dụng taxonomy cho phân tích chính thức, hãy đóng băng phiên bản và duy trì nhật ký thay đổi (changelog).
