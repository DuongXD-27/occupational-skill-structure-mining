# Hướng dẫn chạy pipeline

Khung tích hợp nhận đầu ra crawler và gọi module của từng thành viên, kiểm tra
hợp đồng dữ liệu rồi chuyển bước. Logic làm sạch, regex, trích xuất kỹ năng và
thuật toán RQ nằm trong module của người phụ trách.

```text
crawler output → clean ─┬→ rq1 (Đức)
                       └→ extract (Cường) → analysis / RQ2–RQ4 (Triều)
```

## 1. Cài đặt và kiểm thử sau khi clone

Dùng Python 3.11 trở lên, chạy từ thư mục gốc repo:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-pipeline.txt
.venv\Scripts\python -m pytest tests/integration -q
```

Kiểm thử dùng các module giả lập chép dữ liệu fixture, không tải web hay viết lại
logic của các thành viên. Kết quả này xác nhận điều phối và kiểm tra ranh giới
bàn giao; không chứng minh chất lượng trích xuất hoặc kết luận RQ.

Nếu môi trường chặn thư mục temp hệ thống, tạo thư mục `.tmp` trong repo rồi dùng
`--basetemp .tmp/<tên-mới-cho-lần-chạy>`. Chọn tên mới để tránh pytest xóa thư mục đã tồn tại.

## 2. Tình trạng module hiện tại

`main` có crawler mẫu; chưa có cleaner, skill extractor và analysis thực thi.
Cấu hình [config/pipeline.json](../../config/pipeline.json) dùng dữ liệu mẫu đã có,
nên pipeline không tự gọi crawler hay ghi đè dữ liệu crawl.

Adapter cleaner tham chiếu API quan sát được trên nhánh
`origin/feature/data-cleaner-rq1`: `src.cleaner.pipeline.run_pipeline(input_path, output_path, ...)`.
Nhánh này chưa được merge trong thay đổi tích hợp. RQ1, extractor và analysis
để `null` cho đến khi người phụ trách bàn giao API. Chạy cấu hình này hiện tại
sẽ báo thiếu module; không dùng fixture làm module mặc định.

Cleaner trên nhánh đó cần xử lý các điểm bàn giao trước khi nghiệm thu:
`quality_flags` đang là cột bổ sung, QR-01 có thể bỏ bản ghi, và quy tắc bỏ cấp bậc/
hậu tố công nghệ cần đối chiếu với [quyết định chung](../decisions/integration_decisions.md).
Pipeline sẽ phát hiện schema thay đổi, mất `job_id` hoặc ghi đè trường gốc.
Lương và học vấn không có cột riêng trong schema; crawler không trích xuất riêng,
cleaner không xuất các cột lương/học vấn của schema cũ.
Phần kinh nghiệm chỉ giữ `raw_experience`; cleaner bỏ bước parse số năm và không
xuất hai cột kinh nghiệm phái sinh của schema cũ.

## 3. Cấu hình

`version=1`; `run_kind=integration` cho thử nghiệm, `research` chỉ khi chạy nghiên
cứu với module và dữ liệu thật đã được bàn giao. Tất cả đường dẫn trong `paths`
tính từ thư mục của file cấu hình, không từ thư mục chạy lệnh.
Các đường dẫn đầu vào/đầu ra không được trùng hoặc lồng nhau.

| Khóa | Nội dung |
|---|---|
| `raw` | File JSONL crawler, mặc định mẫu 45 tin; đổi sang `../data/raw/jobs_raw.jsonl` khi có dữ liệu chính thức |
| `clean` | Bảng sạch gồm 22 trường, giữ cả các tin bị đánh cờ |
| `skills` | Bảng `job_id`, `extracted_skills`, `skill_count` |
| `matrix` | Bảng `job_id` và các cột `skill_id` chứa số nguyên 0/1 |
| `taxonomy` | CSV có `skill_id`, `canonical_name` duy nhất, không rỗng |
| `rq1` | Thư mục đầu ra RQ1 và manifest |
| `analysis` | Thư mục đầu ra RQ2–RQ4 và manifest |
| `report` | Báo cáo JSON của lần chạy gần nhất |

Định dạng trao đổi mặc định là Parquet cho bảng sạch/đặc trưng; JSONL cũng được
hỗ trợ khi kiểm thử hoặc chẩn đoán. Văn bản dùng UTF-8. Dữ liệu ngày/dấu thời gian
trong bảng tin tuyển dụng dùng chuỗi ISO như dữ liệu crawler hiện tại; Parquet
cũng chấp nhận kiểu date/timestamp tương đương, không thay đổi giá trị nguồn.

`modules.<stage>` là `module:function`, hoặc `null` nếu chưa bàn giao.
Chỉ dùng cấu hình tin cậy vì entry point được import và thực thi như mã Python.
`options.<stage>` là object JSON được chuyển nguyên vẹn cho module tương ứng;
pipeline không tự diễn giải seed hay ngưỡng nghiên cứu. Module phân tích phải áp
dụng các ngưỡng theo đặc tả; mẫu nhỏ phải trả `skipped` với lý do khi không đủ điều kiện.
Đường dẫn nằm trong `options`, nếu có, do module xử lý; ưu tiên dùng đường dẫn tuyệt đối.

## 4. Chạy riêng từng bước và toàn chuỗi

```powershell
python -m src.pipeline --config config/pipeline.json --stage clean
python -m src.pipeline --config config/pipeline.json --stage rq1
python -m src.pipeline --config config/pipeline.json --stage extract
python -m src.pipeline --config config/pipeline.json --stage analysis
python -m src.pipeline --config config/pipeline.json --stage all
```

`all` chạy `clean → rq1 → extract → analysis`, dừng tại lỗi đầu tiên. Sau khi
cleaner đã xuất dữ liệu sạch, `extract` không cần file raw, crawler hoặc module
RQ1. `analysis` chỉ cần bảng sạch, hai bảng đặc trưng và taxonomy. Thành viên
sửa parser có thể chạy lại `extract` rồi `analysis` mà không crawl/làm sạch lại.

Mã thoát: `0` khi các bước được chọn chạy và đầu ra hợp lệ; `1` khi lỗi cấu hình,
thiếu module, thiếu file hoặc sai hợp đồng. Ví dụ lỗi trước parser:

```text
Không thể chạy skill extraction: thiếu trường relevance_flag ở dòng 1 trong .../jobs_clean.parquet.
```

## 5. API bàn giao cho thành viên

Entry point có dạng `def run(context: StageContext)`. `context.stage` là tên
bước, `context.paths` chứa `Path` cho các artifact, `context.options` chứa cấu
hình bước đó. Hai mapping là chỉ đọc. Module trả về giá trị như sau:

| Bước | Trách nhiệm module | Giá trị trả về |
|---|---|---|
| `clean` | Đọc `raw`, ghi đủ bảng vào `clean`; tạo cờ, title và `job_text` | Không bắt buộc; pipeline tự đếm từ đầu ra |
| `rq1` | Đọc `clean`, ghi kết quả vào thư mục `rq1` | Object trạng thái `RQ1` |
| `extract` | Đọc `clean`, `taxonomy`; ghi `skills`, `matrix` đúng tập tin hợp lệ | Không bắt buộc |
| `analysis` | Đọc `clean`, `skills`, `matrix`, `taxonomy`; ghi kết quả vào `analysis` | Object trạng thái `RQ2`, `RQ3`, `RQ4` |

Ví dụ adapter cho API extractor được bàn giao trong tương lai:

```python
def extract(context):
    from src.parser.skill_extractor import run  # Thay bằng API thật của Cường.
    return run(
        clean_path=context.paths["clean"],
        taxonomy_path=context.paths["taxonomy"],
        skills_path=context.paths["skills"],
        matrix_path=context.paths["matrix"],
        **context.options,
    )
```

Ví dụ trả trạng thái từ module phân tích sau khi đã tạo các file tương ứng:

```json
{
  "RQ2": {"status": "completed", "artifacts": ["skill_frequency.csv"]},
  "RQ3": {"status": "completed", "artifacts": ["title_similarity.csv"]},
  "RQ4": {"status": "skipped", "reason": "Chưa đủ 300 tin để phân cụm.", "artifacts": []}
}
```

`completed` phải có file không rỗng; `skipped` phải có lý do. `artifacts` dùng
đường dẫn tương đối nằm trong thư mục đầu ra của bước. Pipeline tạo `manifest.json`
từ kết quả trả về. Không hard-code đường dẫn đầu ra: pipeline truyền đường dẫn
tạm và chỉ xuất bản kết quả sau khi kiểm tra xong. File phân tích phải được tạo
trong thư mục tạm mà context cung cấp, gồm cả bảng và biểu đồ.

## 6. Kiểm tra và báo cáo

Các kiểm tra chính: đủ 22 trường, đúng kiểu/giá trị bắt buộc, `job_id` duy nhất,
cờ relevance/duplicate đã gán boolean, lý do loại trừ, `job_text` và title chuẩn
hóa cho tin hợp lệ, bảo toàn trường gốc và tập ID từ raw sang clean. Cleaner
giữ `null` cho trường tùy chọn, không xóa tin bị loại khỏi bảng kiểm toán.

Extractor phải lọc `relevance_flag=true AND duplicate_flag=false`; pipeline chỉ
kiểm tra tập ID đầu ra, không tự làm lại quy tắc lọc/chuẩn hóa của thành viên.
`extracted_skills` là danh sách canonical names duy nhất; không tìm thấy kỹ năng
thì `[]`, `skill_count=0`. Ma trận chỉ dùng cột `skill_id` thuộc taxonomy; các cột
toàn 0 có thể bỏ. Ma trận và danh sách kỹ năng phải khớp chính xác từng tin.
Bảng rỗng bị chặn để tránh tạo một lần nghiệm thu không có dữ liệu.

Báo cáo `report` ghi thời gian UTC, hash cấu hình và từng file đầu vào, số bản ghi,
trạng thái các bước, trạng thái RQ và người phụ trách. Các số `duplicates` và
`out_of_scope` có thể giao nhau, nên:

```text
clean_records = valid_records + duplicates + out_of_scope - overlap
```

RQ/bước không chạy trong lần này có trạng thái `not_run`; báo cáo không kế thừa
trạng thái thành công từ lần trước. `research_acceptance=true` chỉ khi chọn
`run_kind=research`, chạy `all` thành công và cả bốn RQ đều `completed`. Cờ này
xác nhận điều kiện thực thi; Dương vẫn phải nghiệm thu chất lượng module, benchmark
trích xuất và tính phù hợp của kết luận theo đặc tả.

Nếu lỗi sau khi đọc cấu hình thành công, báo cáo vẫn được ghi. Lỗi ngay khi đọc
cấu hình thì chỉ in lỗi vì chưa xác định được vị trí báo cáo đáng tin cậy.
Hash phát hiện module sửa đầu vào nhưng không phục hồi file nếu module vi phạm.
Đầu ra đã có chỉ được thay sau khi toàn bộ hợp đồng của bước đạt; việc xuất bản
nhiều file không phải một giao dịch filesystem nguyên tử, nên lỗi I/O giữa chừng
có thể để lại một phần đầu ra mới. File cũ trong thư mục phân tích không tự xóa;
chỉ các artifact ghi trong manifest của lần chạy mới thuộc kết quả hiện tại.

Xem [báo cáo bàn giao tích hợp](../../reports/integration/acceptance.md) để biết
phần đã kiểm chứng và các điều kiện còn thiếu cho nghiệm thu chính thức.
