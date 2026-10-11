# ĐẶC TẢ LƯỢC ĐỒ DỮ LIỆU (DATA SCHEMA)

## 1. Mục đích

Tài liệu này định nghĩa cấu trúc dữ liệu thống nhất cho toàn bộ dự án.

## 2. Quy ước chung

Tên trường (Field Names): Sử dụng định dạng `snake_case`.

Dữ liệu văn bản (Text): Lưu trữ dưới dạng mã hóa UTF-8, không xóa dấu tiếng Việt khỏi dữ liệu thô.

Giá trị bị thiếu (Missing Values): Sử dụng `null` cho dữ liệu bị thiếu, không tự ý sử dụng các giá trị giữ chỗ (placeholders) như: "N/A", "unknown", "-", "none", trừ khi đó là chuỗi văn bản thô nguyên bản thu được trực tiếp từ trang nguồn và được lưu trữ bên trong một trường thô (raw field).

Ngày tháng (Dates): Sử dụng định dạng `YYYY-MM-DD`

Dấu thời gian (Timestamps): Sử dụng định dạng ISO 8601 và bao gồm múi giờ bất cứ khi nào có sẵn.

Giá trị Boolean: Chỉ sử dụng: `true`/`false`

Kinh nghiệm (Experience): Chỉ lưu `raw_experience: string/null`, giữ nguyên văn bản nguồn nếu có; nếu thiếu thì dùng `null`.

Dữ liệu thô (Raw Data): Không được ghi đè các trường thô bằng dữ liệu đã chuẩn hóa hoặc dữ liệu phái sinh.

## 3. Các giai đoạn dữ liệu (Data Stages)

Dự án bao gồm bốn giai đoạn dữ liệu chính:

**Giai đoạn A — Dữ liệu thô (Stage A — Raw data)**: Dữ liệu được trích xuất trực tiếp từ các nguồn tuyển dụng bởi các bộ bóc tách (parsers).

**Giai đoạn B — Dữ liệu sạch (Stage B — Clean data)**: Dữ liệu đã được làm sạch, chuẩn hóa và gắn chú thích các cờ mức độ liên quan (relevance) và cờ trùng lặp (duplicate).

**Giai đoạn C — Đặc trưng kỹ năng (Stage C — Skill features)**: Dữ liệu đã được trích xuất các kỹ năng chuẩn hóa.

**Giai đoạn D — Đầu ra phân tích (Stage D — Analysis outputs)**: Các bảng dữ liệu phái sinh phục vụ đo lường độ tương đồng, phân cụm và trực quan hóa.

## 4. Lược đồ tin tuyển dụng chính (Main Vacancy Schema)

| Tên trường (Field) | Mô tả | Kiểu dữ liệu (Type) | Bắt buộc? | Nguồn gốc | Được chuẩn hóa? |
|---|---|---|---|---|---|
| `job_id` | Khóa định danh nội bộ duy nhất | string | Có | Phái sinh (Derived) | Không |
| `source` | Nền tảng / nguồn tuyển dụng | string | Có | Thô (Raw) | Không |
| `source_job_id` | ID tin tuyển dụng từ website nguồn nếu có | string/null | Không | Thô (Raw) | Không |
| `source_url` | URL trang chi tiết tin tuyển dụng | string | Có | Thô (Raw) | Không |
| `crawl_timestamp` | Dấu thời gian thu thập dữ liệu | datetime | Có | Thô (Raw) | Không |
| `parser_version` | Phiên bản parser thu thập | string | Có | Thô (Raw) | Không |
| `raw_job_title` | Chức danh công việc nguyên bản | string | Có | Thô (Raw) | Không |
| `normalized_job_title` | Chức danh đã chuẩn hóa bề mặt | string/null | Sau làm sạch | Phái sinh (Derived) | Có |
| `company` | Tên công ty tuyển dụng | string/null | Không | Thô (Raw) | Hạn chế |
| `raw_location` | Chuỗi địa điểm nguyên bản | string/null | Không | Thô (Raw) | Không |
| `normalized_location` | Địa điểm đã chuẩn hóa | string/null | Không | Phái sinh (Derived) | Có |
| `posted_date` | Ngày đăng tuyển nếu có | date/null | Không | Thô/Parse | Chỉ chuẩn hóa định dạng |
| `raw_experience` | Chuỗi yêu cầu kinh nghiệm nguyên bản | string/null | Không | Thô (Raw) | Không |
| `job_description` | Văn bản mô tả công việc | string/null | Có điều kiện | Thô (Raw) | Không |
| `job_requirements` | Văn bản yêu cầu ứng viên | string/null | Có điều kiện | Thô (Raw) | Không |
| `job_text` | Văn bản nối phục vụ trích xuất kỹ năng | string/null | Sau tiền xử lý | Phái sinh (Derived) | Có |
| `relevance_flag` | Đánh dấu tin có thuộc phạm vi nghiên cứu | boolean | Sau làm sạch | Phái sinh (Derived) | Không |
| `exclusion_reason` | Lý do loại trừ nếu tin không liên quan | string/null | Khi relevance=false | Phái sinh (Derived) | Không |
| `duplicate_flag` | Đánh dấu bản ghi có bị trùng lặp không | boolean | Sau làm sạch | Phái sinh (Derived) | Không |
| `duplicate_group_id` | ID nhóm nhận diện các tin trùng lặp | string/null | Không | Phái sinh (Derived) | Không |
| `extracted_skills` | Danh sách các kỹ năng chuẩn hóa trích xuất | list[string]/null | Sau trích xuất | Phái sinh (Derived) | Có |
| `skill_count` | Số lượng kỹ năng trích xuất được | integer/null | Sau trích xuất | Phái sinh (Derived) | Không |

**Quy tắc đối với tin tuyển dụng hợp lệ:** Một tin tuyển dụng hợp lệ bắt buộc phải chứa `raw_job_title` và ít nhất một trong hai trường văn bản: `job_description` hoặc `job_requirements`. Nếu cả hai trường văn bản đều trống, bản ghi thiếu dữ liệu tối thiểu cho việc trích xuất kỹ năng và phải được xem xét loại trừ.

**Quy tắc đối với job_id:** `job_id` đóng vai trò là khóa chính nội bộ (internal primary key) của dự án. Nó phải:

- là duy nhất;
- ổn định qua các lần thực thi pipeline;
- độc lập với chỉ số dòng (row index / line numbers);
- không thể thay đổi (immutable) sau khi làm sạch.

Nếu website nguồn cung cấp mã tin tuyển dụng, hãy lưu riêng vào trường `source_job_id`. Không sử dụng `source_job_id` của một website cụ thể làm khóa chính toàn cục cho toàn bộ dự án.

**Quy tắc cho Chức danh công việc:** `raw_job_title` phải giữ nguyên nội dung thô chính xác thu được từ nguồn. Không sửa lỗi chính tả hoặc gộp nghề nghiệp bên trong trường này. Không ghép skill tags hoặc metadata từ vùng khác vào chức danh. Nếu phần công nghệ đã nằm trong chức danh nguồn, phải bảo toàn phần đó trong `raw_job_title`.

**Quy tắc chuẩn hóa (normalized_job_title):** Chỉ được dùng để loại bỏ các điểm sai lệch về bề mặt và định dạng, tuyệt đối không tự động gộp các vị trí:

- AI Engineer
- Machine Learning Engineer
- Data Scientist

thành một nhóm nghề nghiệp chung. Việc gom nhóm ngữ nghĩa không thuộc về giai đoạn làm sạch dữ liệu.

**Quy tắc cho Địa điểm:**

Phải lưu giữ `raw_location` và nếu có thể chuẩn hóa được, bổ sung thêm `normalized_location`. Không được ghi đè lên `raw_location`.

**Quy tắc cho Kinh nghiệm:** Chỉ giữ `raw_experience: string/null`. Có thông tin
nguồn thì lưu nguyên văn, ví dụ `2–4 years of experience`, `3+ years` hoặc
`Fresh graduates are welcome`; không có thì dùng `null`. Không bóc tách số năm
tối thiểu/tối đa hoặc quy đổi cấp bậc thành số năm. RQ1–RQ4 không dùng số năm
kinh nghiệm; chỉ bổ sung trường phái sinh khi phạm vi nghiên cứu cần đến chúng.


## 10. Phạm vi lương và học vấn

Schema hiện tại gồm 22 trường, không có trường lương hoặc học vấn vì không phục vụ
RQ1–RQ4. Crawler không trích xuất riêng các thông tin này; cleaner không tạo hoặc
xuất cột tương ứng. Không yêu cầu truy cập thông tin lương cần đăng nhập.

Văn bản mô tả và yêu cầu từ nguồn vẫn được bảo toàn, kể cả khi chứa thông tin lương
hoặc học vấn. Chỉ xem xét thêm trường riêng khi phạm vi nghiên cứu thay đổi.

---

## 11. Quy tắc cho Mức độ liên quan (Relevance)

`relevance_flag = true`:

Tin tuyển dụng được giữ lại trong tập dữ liệu nghiên cứu.

`relevance_flag = false`:

Tin tuyển dụng bị loại khỏi các phân tích chính.

Khi `relevance_flag = false`:

`exclusion_reason` là bắt buộc phải có.

Lý do loại trừ phải lấy từ một tập nhãn chuẩn hóa, định sẵn thay vì các đoạn bình luận tự do tùy tiện.

---

## 12. Quy tắc cho Trùng lặp (Duplicates)

Không xóa các bản ghi trùng lặp khỏi tập dữ liệu thô.

Đánh dấu các bản ghi trùng lặp bằng:

`duplicate_flag`

và khi áp dụng được:

`duplicate_group_id`.

Tập dữ liệu nghiên cứu cuối cùng sẽ chỉ giữ lại một bản ghi đại diện cho mỗi vị trí tuyển dụng duy nhất sau khi quá trình khử trùng lặp hoàn tất.

---

## 13. Quy tắc cho extracted_skills

`extracted_skills` chỉ chứa các tên kỹ năng chuẩn hóa (canonical names) được định nghĩa trong taxonomy của dự án.

Không cho phép biểu diễn lẫn lộn, ví dụ:

AWS  
Amazon Web Services  

nếu cả hai đều đã được định nghĩa là cùng một kỹ năng chuẩn.

Danh sách kỹ năng phải tham chiếu đến taxonomy đang hoạt động của dự án.

---

## 14. Ma trận kỹ năng (Skill Matrix)

Ma trận kỹ năng được lưu trữ tách biệt với bảng tin tuyển dụng chính.

Mỗi dòng tương ứng với một `job_id`.

Lược đồ cơ bản:

`job_id`  
`skill_001`  
`skill_002`  
...  
`skill_n`  

Giá trị ô:

1 = kỹ năng xuất hiện  
0 = bộ trích xuất không phát hiện kỹ năng  

Tên hoặc mã định danh kỹ năng phải tham chiếu chuẩn xác đến taxonomy.

Hợp đồng tích hợp hiện tại dùng `skill_id` làm tên cột ma trận và
`canonical_name` trong `extracted_skills`; hai dạng được đối chiếu qua cùng file
taxonomy. Danh sách không có kỹ năng là `[]` với `skill_count=0`, không phải `null`.

---

## 15. Lược đồ Nhật ký thu thập (Crawl Log Schema)

File nhật ký thu thập (crawl log) phải chứa tối thiểu các trường sau:

| Trường (Field) | Mô tả | Kiểu dữ liệu | Bắt buộc? |
|---|---|---|---|
| `source` | Nền tảng nguồn tuyển dụng | string | Có |
| `source_url` | URL đã truy cập | string | Có |
| `crawl_timestamp` | Dấu thời gian truy cập | datetime | Có |
| `status` | Trạng thái thành công / thất bại | string | Có |
| `http_status` | Mã trạng thái HTTP nếu có | integer/null | Không |
| `error_type` | Loại phân loại lỗi | string/null | Không |
| `error_message` | Mô tả lỗi ngắn gọn | string/null | Không |
| `parser_version` | Phiên bản của parser | string | Có |

---

## 16. Các file dữ liệu tiêu chuẩn giữa các module

### Dữ liệu thô (Raw data)

`data/raw/jobs_raw.jsonl`

Bên sản xuất: Module Thu thập dữ liệu (Data Collection).

Tuyệt đối không được chỉnh sửa trực tiếp sau khi ghi.

### Dữ liệu sạch (Clean data)

`data/processed/jobs_clean.parquet`

Bên sản xuất: Module Làm sạch dữ liệu (Data Cleaning).

Đây là tập dữ liệu chính được sử dụng bởi tất cả các module hạ nguồn.

### Taxonomy kỹ năng

`taxonomy/skills_taxonomy.csv`

Bên sản xuất: Module Trích xuất kỹ năng (Skill Extraction).

### Dữ liệu kỹ năng việc làm (Job skill data)

`data/features/job_skills.parquet`

Các trường bắt buộc:

`job_id`  
`extracted_skills`  
`skill_count`  

### Ma trận kỹ năng việc làm (Job skill matrix)

`data/features/job_skill_matrix.parquet`

Các trường bắt buộc:

`job_id`  
các cột kỹ năng  

---

## 17. Các trường bắt buộc giữ nguyên bản (Untouched Fields)

Các trường sau đây không bao giờ được phép ghi đè:

`source`  
`source_job_id`  
`source_url`  
`crawl_timestamp`  
`raw_job_title`  
`raw_location`  
`raw_experience`  
`job_description`  
`job_requirements`  

Nếu cần biến đổi dữ liệu, hãy tạo các trường phái sinh mới.

---

## 18. Các trường được phép chuẩn hóa

Các trường phái sinh được phép chuẩn hóa:

`normalized_job_title`  
`normalized_location`  
`job_text`  
`extracted_skills`  

Mọi quy tắc chuẩn hóa quan trọng đều phải có tài liệu hoặc file ánh xạ tương ứng.

---

## 19. Giao thức thay đổi lược đồ (Schema Change Protocol)

Một khi Lược đồ dữ liệu đã được Trưởng nhóm (Leader) khóa:

- Không tự ý thêm trường;
- Không tự ý xóa trường;
- Không tự ý đổi tên trường;
- Không tự ý thay đổi kiểu dữ liệu.

Nếu việc thay đổi schema là cần thiết, thành viên phải báo cáo:

1. Trường dữ liệu mục tiêu;
2. Cơ sở / lý do đề xuất;
3. Các module hạ nguồn bị ảnh hưởng;
4. Chiến lược xử lý đối với dữ liệu cũ (legacy data).

Cần có sự phê duyệt của Leader trước khi ban hành thay đổi schema tiếp theo.

---

## 20. Nguyên tắc quản lý thay đổi lược đồ

Các bản cập nhật nhỏ cần đảm bảo tính tương thích ngược: giữ nguyên cấu trúc cốt lõi và không làm gián đoạn các module phụ thuộc.

Các thay đổi lớn phá vỡ tính tương thích ảnh hưởng đến cấu trúc schema hoặc các module phụ thuộc cần có kế hoạch di chuyển (migration) dữ liệu rõ ràng.

Tất cả các tập dữ liệu được sử dụng để tạo ra kết quả nghiên cứu chính đều phải ghi nhận rõ lược đồ schema được áp dụng.
