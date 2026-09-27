# Khai Phá Cấu Trúc Kỹ Năng Nghề Nghiệp Data/AI (Occupational Skill Structure Mining)

**Học phần:** IT4142E - Khoa học Dữ liệu (Data Science)  
**Kho lưu trữ:** [DuongXD-27/occupational-skill-structure-mining](https://github.com/DuongXD-27/occupational-skill-structure-mining)

---

## 1. Tổng quan dự án

Dự án **"Vietnam Data & AI Job Skill Landscape 2026: Khai phá cấu trúc nghề nghiệp và nhu cầu kỹ năng Data/AI tại Việt Nam năm 2026 từ dữ liệu tuyển dụng trực tuyến tự thu thập"** tập trung xây dựng một pipeline Khoa học Dữ liệu hoàn chỉnh từ đầu đến cuối (end-to-end):
- Thu thập dữ liệu tin tuyển dụng thực tế trong lĩnh vực Dữ liệu và Trí tuệ nhân tạo (Data/AI) từ các cổng tuyển dụng công khai.
- Làm sạch, chuẩn hóa và kiểm soát chất lượng dữ liệu theo quy chuẩn chặt chẽ.
- Trích xuất kỹ năng kỹ thuật dựa trên bộ từ vựng kỹ năng (taxonomy) được kiểm chứng thực nghiệm.
- Phân tích thống kê mô tả, tần suất kỹ năng, độ đồng xuất hiện (co-occurrence) và độ phân tán nội bộ chức danh.
- Phân cụm việc làm dựa trên không gian kỹ năng thuần túy và đối chiếu các cụm phát hiện được với chức danh thị trường thực tế.

---

## 2. Cấu trúc thư mục

```text
├── data/
│   ├── pilot/                   # Dữ liệu phục vụ đợt thu thập thử nghiệm mở rộng
│   └── sample/                  # Mẫu dữ liệu ban đầu
│       ├── crawl_log_sample.csv # Nhật ký thu thập dữ liệu mẫu
│       └── sample_jobs.jsonl    # 45 tin tuyển dụng mẫu dạng JSON Lines
├── docs/                        # Tài liệu đặc tả và hướng dẫn
│   ├── project_scope.md         # Phạm vi dự án, mục tiêu và 4 câu hỏi nghiên cứu
│   ├── data_schema.md           # Đặc tả lược đồ dữ liệu chuẩn (29 trường)
│   ├── data_collection/
│   │   └── source_inspection.md # Báo cáo khảo sát và đánh giá nguồn tuyển dụng
│   ├── skill_extraction/
│   │   └── annotation_guideline.md # Hướng dẫn định nghĩa và gán nhãn kỹ năng kỹ thuật
│   ├── data_cleaning/
│   │   ├── data_quality_rules.md   # Bộ quy tắc làm sạch và kiểm soát chất lượng dữ liệu
│   │   └── location_mapping.csv    # Bảng ánh xạ chuẩn hóa địa danh hành chính
│   └── analysis/
│       └── analysis_spec.md     # Đặc tả phương pháp tính toán và chỉ số phân tích
├── notebooks/                   # Jupyter Notebooks phục vụ EDA và thử nghiệm
├── reports/                     # Các báo cáo đánh giá chất lượng và phân tích
│   ├── analysis/
│   │   └── sample_analysis_check.md # Báo cáo kiểm tra tính khả thi của dữ liệu mẫu
│   └── data_quality/
│       └── sample_data_profile.csv  # Bảng hồ sơ chất lượng dữ liệu mẫu
├── scripts/                     # Các script tiện ích và tự động hóa
│   └── recount_taxonomy.py      # Script kiểm tra và tính toán lại tần suất taxonomy
├── src/                         # Mã nguồn chính của dự án
│   ├── crawler/                 # Module thu thập dữ liệu (Scraper/Crawler)
│   │   └── sample_crawler.py    # Crawler thu thập dữ liệu mẫu từ ITviec
│   └── parser/                  # Module bóc tách và tiền xử lý văn bản
└── taxonomy/                    # Bộ từ vựng kỹ năng chuẩn hóa
    └── skills_taxonomy.csv      # Bảng 246 kỹ năng kỹ thuật được quan sát thực tế
```

---

## 3. Các tài liệu đặc tả cốt lõi

1. **Phạm vi nghiên cứu:** [docs/project_scope.md](docs/project_scope.md) — Khóa 4 câu hỏi nghiên cứu (RQ1–RQ4), tiêu chí xác định vị trí Data/AI hợp lệ, tiêu chuẩn giữ/loại tin và nguồn dữ liệu (chính: ITviec, dự phòng: TopCV).
2. **Lược đồ dữ liệu:** [docs/data_schema.md](docs/data_schema.md) — Quy chuẩn 29 trường dữ liệu qua 4 giai đoạn xử lý, nguyên tắc bảo toàn dữ liệu thô và định dạng trao đổi giữa các module.
3. **Khảo sát nguồn:** [docs/data_collection/source_inspection.md](docs/data_collection/source_inspection.md) — Đánh giá chi tiết cấu trúc DOM, JSON-LD, phân trang và tính khả thi của cổng ITviec.
4. **Hướng dẫn gán nhãn kỹ năng:** [docs/skill_extraction/annotation_guideline.md](docs/skill_extraction/annotation_guideline.md) — Định nghĩa kỹ năng kỹ thuật, quy tắc bao hàm/loại trừ, xử lý từ đồng nghĩa, từ viết tắt và kỹ năng ngầm.
5. **Quy tắc chất lượng dữ liệu:** [docs/data_cleaning/data_quality_rules.md](docs/data_cleaning/data_quality_rules.md) — Hệ thống quy tắc làm sạch dữ liệu từ QR-01 đến QR-06, xử lý missing value, chuẩn hóa địa điểm/kinh nghiệm/chức danh và phát hiện trùng lặp.
6. **Đặc tả phân tích:** [docs/analysis/analysis_spec.md](docs/analysis/analysis_spec.md) — Phương pháp luận tính toán chỉ số cho RQ1 (cấu trúc thị trường), RQ2 (tần suất & co-occurrence), RQ3 (độ tương đồng chức danh) và RQ4 (phân cụm không giám sát & PCA).

---

## 4. Hướng dẫn chạy và kiểm thử

### Kiểm tra tính nhất quán của Taxonomy
Chạy script sau từ thư mục gốc của repository để xác thực rằng toàn bộ 246 kỹ năng trong taxonomy đều xuất hiện trong tập dữ liệu mẫu và có số lần quan sát chính xác:

```bash
python scripts/recount_taxonomy.py --check
```

### Thu thập dữ liệu mẫu
Để chạy crawler thu thập dữ liệu mẫu từ ITviec:

```bash
python src/crawler/sample_crawler.py
```
Dữ liệu thu thập sẽ được ghi vào `data/sample/sample_jobs.jsonl` và nhật ký sẽ ghi vào `data/sample/crawl_log_sample.csv`.
