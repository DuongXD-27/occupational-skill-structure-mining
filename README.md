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
├── report/main.tex      # BÁO CÁO DUY NHẤT: phạm vi, quy định, quyết định, phương pháp, kết quả
├── config/              # Cấu hình đường ống, bảng ánh xạ địa điểm
├── data/
│   ├── sample/          # 45 tin mẫu dùng xây taxonomy
│   ├── pilot/           # Đợt thu 30/09/2026 (252 tin)
│   ├── evaluation/      # Gold kỹ năng 50 tin, góp ý rà soát, tệp duyệt
│   └── labels/          # Mẫu và tệp gán nhãn vai trò
├── notebooks/           # EDA và phân tích
├── scripts/             # Gộp đợt thu, đếm lại taxonomy, gộp nhãn, chạy phân tích
├── src/                 # crawler, cleaner, parser, analysis, pipeline
├── taxonomy/            # 246 kỹ năng chuẩn, danh sách công cụ ngoài taxonomy
├── tests/               # Kiểm thử
└── tools/               # Trang duyệt gold và trang gán nhãn vai trò (chạy offline)
```

Dữ liệu thô, dữ liệu đã xử lý và đầu ra phân tích (`data/raw/`, `data/processed/`, `data/features/`,
`reports/`) được sinh khi chạy và không có trên GitHub.

---

## 3. Tài liệu

Toàn bộ phạm vi, lược đồ dữ liệu, quy tắc chất lượng, hướng dẫn gán nhãn (kỹ năng và vai trò), đặc tả
phân tích, giao thức đánh giá, nhật ký quyết định và kết quả nằm trong **một tài liệu duy nhất**:
[`report/main.tex`](report/main.tex). Biên dịch bằng XeLaTeX:

```bash
cd report && latexmk -xelatex main.tex
```

Khi có quyết định mới, sửa trực tiếp báo cáo và ghi vào phụ lục «Nhật ký quyết định».
Không tạo thêm tệp README hay Markdown rải rác trong repo.

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

### Điều phối pipeline và kiểm thử tích hợp

```powershell
python -m pip install -r requirements.txt
python -m pytest tests/integration -q
python -m src.pipeline --config config/pipeline.json --stage extract
```

Khung tích hợp nằm ở `src/pipeline/`, hỗ trợ chạy riêng `clean`, `rq1`, `extract`,
`analysis` hoặc toàn chuỗi với `--stage all`. Cấu hình `config/pipeline.json` gọi
module thật của cleaner/RQ1 (`src/cleaner`), parser (`src/parser`) và phân tích
(`src/analysis`). Kiểm thử tích hợp dùng module giả lập, không thay thế nghiệm thu nghiên cứu.

Phân công, hợp đồng giữa các khâu và API bàn giao: `report/main.tex` mục 4.1.

### Trích xuất kỹ năng và đánh giá

```powershell
python -m pip install -r requirements.txt
python -m pytest tests/parser -q
python -m src.parser preview --input data/sample/sample_jobs.jsonl --output-dir data/features/development
python -m src.parser evaluate --gold data/evaluation/gold_jobs.draft.jsonl --output-dir reports/skill_extraction/tune --subset tune
```

Recount và pipeline dùng chung matcher trong `src/parser/`. Gold kỹ năng, quy trình duyệt, chia
tune/holdout và kết quả P/R/F1: `report/main.tex` mục 4.4 và 5.1. Nhãn nháp do trợ lý gán, chờ người duyệt.
