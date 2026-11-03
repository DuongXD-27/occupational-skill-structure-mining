# Sử dụng bộ trích xuất kỹ năng

`src/parser/skill_extractor.py` là thuật toán duy nhất. Nó tải CSV taxonomy,
chuẩn hóa NFKC, tìm canonical/alias/abbreviation với word boundary, kiểm tra ngữ
cảnh CV, giải quyết overlap theo độ dài rồi khử trùng kỹ năng theo tài liệu.
`scripts/recount_taxonomy.py` gọi lại các hàm này; không duy trì matcher riêng.

```python
from src.parser import extract_skills, SkillExtractor

skills = extract_skills("Experience in Python, SQL Server and Power BI.")
# ['Microsoft SQL Server', 'Power BI', 'Python']
extractor = SkillExtractor()  # Tải taxonomy một lần khi xử lý nhiều tin.
skills = extractor.extract("Send us your CV.")  # []
```

Output dùng canonical names và thứ tự CSV ổn định. C/R/Go canonical có phân biệt
hoa/thường; C không khớp bên trong C++/C#, R không khớp R&D. CV cần ngữ cảnh vision;
giới hạn xử lý ngữ cảnh/phủ định được ghi trong báo cáo. Tên kỹ năng mới chỉ được
thêm qua taxonomy và quy trình quản lý thay đổi, không thêm danh sách trong code.

## Cài và kiểm thử

```powershell
python -m pip install -r requirements-parser.txt
python -m pytest tests/parser -q
python scripts/recount_taxonomy.py --check
```

Ba testcase `xfail(strict=True)` giữ lại giới hạn đã biết: phủ định, Go ở đầu câu
và CV hồ sơ trong tài liệu có ngữ cảnh vision. Chúng cần trở thành pass khi sửa
thuật toán, thay vì bị bỏ khỏi báo cáo.

## Thử raw và xuất artifact từ clean

```powershell
python -m src.parser preview --input data/sample/sample_jobs.jsonl --output-dir data/features/development
python -m src.parser extract --input data/processed/jobs_clean.parquet --output-dir data/features
```

Preview không cần cleaner, giữ toàn bộ tin raw và dùng tiền tố `sample_` trong
thư mục `development`. Các artifact này chỉ để phát triển, không dùng làm số
liệu RQ2–RQ4. Manifest ghi rõ `raw_preview` và `research_acceptance=false`.

Lệnh extract cần boolean thật cho `relevance_flag`, `duplicate_flag` ở mọi dòng,
chỉ giữ `relevance_flag=true AND duplicate_flag=false`. Mỗi tin hợp lệ xuất một
dòng trong `job_skills.parquet` với `extracted_skills: list[string]`,
`skill_count: int32`. Không khớp kỹ năng thì `[]`/0. Ma trận `job_skill_matrix.parquet`
có `job_id` và các cột **skill_id** của taxonomy, giá trị `uint8` 0/1; canonical
names dùng trong danh sách, không làm tên cột ma trận. Hai bảng có cùng thứ tự/tập
ID, gồm cả tin không có kỹ năng; input rỗng, trùng ID hoặc tin thiếu cả hai trường
văn bản bị từ chối. JSONL cũng được hỗ trợ khi chẩn đoán.

Parser không crawl, làm sạch hoặc tự gán cờ. Tại main hiện tại chưa có clean được
bàn giao/nghiệm thu. File trên nhánh cleaner chưa được coi là bàn giao chính thức,
nên PR này chỉ xuất hai bảng preview, không công bố artifact chính thức cho Triều.
Khi Đức bàn giao clean, chạy extract và chuyển cả hai bảng cùng manifest cho Triều.
Đầu ra được ghi qua file tạm; thay hai file không phải một giao dịch I/O nguyên tử.

## API pipeline

`src.parser.features:run` nhận `StageContext` có các path `clean`, `taxonomy`,
`skills`, `matrix` và mapping `options`. Entry point luôn dùng cờ sạch, không cho
bật preview. Khi khung pipeline của **PR #15** được merge, đặt:

```json
"extract": "src.parser.features:run"
```

trong `modules` của `config/pipeline.json`. Main dùng làm base PR parser chưa có
file cấu hình này; PR parser không tự merge các PR thành viên hoặc PR #15.

## Đánh giá

```powershell
python -m src.parser evaluate --gold data/evaluation/gold_jobs.draft.jsonl --output-dir reports/skill_extraction/draft_gold
```

Kết quả gồm micro TP/FP/FN, Precision/Recall/F1, thống kê từng kỹ năng, predictions
và danh sách lỗi từng tin. Nhãn gold luôn được đối chiếu canonical names/skill IDs
và đoạn bằng chứng; metadata không được tự đổi thành human reviewed. Xem
[báo cáo](../../reports/skill_extraction/evaluation.md) và
[gold README](../../data/evaluation/README.md) trước khi dùng số liệu.
