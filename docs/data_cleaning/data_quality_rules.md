# Bộ Quy tắc Chất lượng Dữ liệu (Data Quality Rules)

## 1. Nguyên tắc Bất biến của Dữ liệu thô & Cấu trúc Trường chuẩn

### 1.1 Nguyên tắc Bất biến của Dữ liệu thô (Raw Data Immutability Principle)

1. **Dữ liệu thô là bất biến:** Tất cả các trường dữ liệu thu nhận trực tiếp từ crawler (`Giai đoạn A - Các trường thô` như `raw_job_title`, `raw_location`, `raw_experience`, `job_description`, `job_requirements`, `source_url`...) không bao giờ được phép sửa đổi, cắt tỉa (trim), hoặc ghi đè tại chỗ trong cơ sở dữ liệu hay bộ nhớ thô.
2. **Phân tách tuyệt đối giữa Dữ liệu thô và Dữ liệu phái sinh:** Mọi thao tác làm sạch, chuẩn hóa, bóc tách số liệu hoặc định dạng đều phải xuất kết quả ra các trường phái sinh mới được tạo (`Giai đoạn B - Các trường phái sinh`). Dữ liệu thô ban đầu vẫn được giữ nguyên vẹn 100% bên cạnh các thuộc tính đã làm sạch.
3. **Đánh cờ trạng thái thay vì xóa vật lý:** Các bản ghi chứa lỗi, bản ghi trùng lặp hoặc nằm ngoài phạm vi nghiên cứu tuyệt đối không bị xóa vật lý khỏi tập dữ liệu phân tích. Thay vào đó, trạng thái của chúng được gắn nhãn thông qua các trường chỉ báo chuyên dụng (`relevance_flag`, `exclusion_reason`, `duplicate_flag`, `duplicate_group_id`). Quy định này đảm bảo tính kiểm toán, tính minh bạch và khả năng tái lập nghiên cứu.

### 1.2 Tuân thủ Cấu trúc Lược đồ chuẩn

- **Các trường thô (Giai đoạn A):** Được thu thập ở định dạng nguyên bản bởi crawler; được pipeline làm sạch coi là chỉ đọc (read-only).
- **Các trường phái sinh (Giai đoạn B) do Pipeline làm sạch tạo ra:**
  - `normalized_location` (chuẩn hóa từ `raw_location` qua QR-02)
  - `experience_min_years`, `experience_max_years` (bóc tách từ `raw_experience` qua QR-03)
  - `normalized_job_title` (làm sạch bề mặt từ `raw_job_title` qua QR-04)
  - `duplicate_flag`, `duplicate_group_id` (đánh cờ qua QR-05)
  - `relevance_flag`, `exclusion_reason` (đánh cờ qua QR-06 và QR-01)

> **Lưu ý về đề xuất trường `quality_flags` [Cần gửi yêu cầu thay đổi Schema]:** Trường `quality_flags` (dự kiến dùng để lưu trữ các cờ lỗi chi tiết nội bộ như `MISSING_*`, `LOCATION_UNRECOGNIZED`...) hiện chưa nằm trong `docs/data_schema.md §4`.
> - **Đề xuất:** Bổ sung `quality_flags: list[string]` vào schema v1.1.
> - **Chiến lược dự phòng:** Nếu không được phê duyệt, các cờ chất lượng sẽ được ghi vào một file log chuyên dụng (`data/logs/quality_flags.jsonl`) thay vì đưa trực tiếp vào schema chính của dataset.

---

## 2. QR-01: Quy tắc Xử lý Giá trị bị thiếu (Missing Value Handling Rules)

### 2.1 Định nghĩa "Bị thiếu" (Missing)

Một trường được coi là bị thiếu nếu giá trị của nó là `null` hoặc là chuỗi rỗng/chỉ chứa khoảng trắng sau khi cắt tỉa (trim).

> **Ghi chú theo Schema (§2):** Nếu một trường thô chứa một chuỗi giữ chỗ nguyên bản lấy trực tiếp từ website nguồn (ví dụ: "N/A" hoặc "Negotiable"), đây **không bị coi là missing** trong giai đoạn thô — nó đại diện cho nội dung thô thực tế. Một trường chỉ được đánh dấu là missing khi không có dữ liệu nào được chuyển giao.

### 2.2 Xử lý theo từng trường cụ thể

| Trường (Tên chuẩn theo Schema) | Hành động khi bị thiếu | Cờ lỗi (Error Flag) |
|---|---|---|
| `raw_job_title` | **Loại bỏ bản ghi** — không có chức danh, tin tuyển dụng không thể phân tích | `MISSING_JOB_TITLE` |
| `job_description` và `job_requirements` **cùng bị thiếu** | Giữ lại bản ghi; gán `relevance_flag = false`, `exclusion_reason = "INSUFFICIENT_TEXT"` (Phạm vi §7 tiêu chí 5) | `MISSING_TEXT_FIELDS` |
| `job_description` thiếu, nhưng `job_requirements` có | Giữ lại; dùng `job_requirements` để trích xuất kỹ năng | `MISSING_JOB_DESCRIPTION` |
| `job_requirements` thiếu, nhưng `job_description` có | Giữ lại; dùng `job_description` để trích xuất kỹ năng | `MISSING_JOB_REQUIREMENTS` |
| `source` | **Loại bỏ bản ghi** — không thể xác lập nguồn gốc xuất xứ dữ liệu | `MISSING_SOURCE` |
| `source_url` | **Loại bỏ bản ghi** — không thể khử trùng lặp hoặc kiểm toán xuất xứ | `MISSING_SOURCE_URL` |
| `crawl_timestamp` | Giữ lại, ghi nhận cờ; **không tự ý chèn giá trị giả định** | `MISSING_CRAWL_TIMESTAMP` |
| `company` | Giữ lại, ghi nhận cờ; **không tự ý chèn giá trị giả định** | `MISSING_COMPANY` |
| `raw_location` | Giữ lại, đặt `normalized_location = null`; ghi nhận cờ | `MISSING_LOCATION` |
| `raw_experience` | Giữ lại, đặt `experience_min_years = null`, `experience_max_years = null` | `MISSING_EXPERIENCE` |
| `parser_version` | Giữ lại, ghi nhận cờ | `MISSING_PARSER_VERSION` |

> **Tại sao `raw_job_title`, `source`, và `source_url` bị loại bỏ thay vì chỉ gắn cờ:** Ba trường này đại diện cho **các lỗi kỹ thuật nghiêm trọng** (bản ghi không thể định danh, không thể truy vết hoặc không thể khử trùng lặp). Tiêu chí loại trừ của Phạm vi §7 được thiết kế để bảo vệ các bản ghi có ý nghĩa phân tích — không áp dụng cho các bản ghi bị hỏng về mặt kỹ thuật không thể tham chiếu.
>
> **Quy tắc về giá trị giữ chỗ (Schema §2):** Tuyệt đối không điền vào các trường bằng các giá trị nhân tạo như `"Unknown"`, `"N/A"`, `"none"`, hoặc `"-"`. Khi dữ liệu vắng mặt, gán `null`. Trường hợp ngoại lệ duy nhất là khi chuỗi ký tự đó được crawler bóc tách nguyên văn từ nguồn.

### 2.3 Ngưỡng cảnh báo trên toàn bộ Dataset

- Nếu > 10% số bản ghi thiếu cả `job_description` và `job_requirements`: **dừng pipeline và phát cảnh báo cho nhóm**.
- Nếu > 20% số bản ghi thiếu `job_requirements` (trong khi có `job_description`): **ghi log cảnh báo**, nhưng tiếp tục thực thi.
- Nếu > 30% số bản ghi thiếu `raw_location`: **ghi log cảnh báo**, kiểm tra lại bộ chọn (selectors) của crawler.

### 2.4 Xử lý Lỗi thu thập (Scraping Error Handling - Phạm vi §7: "Trang lỗi, liên kết hỏng")

Lỗi thu thập thuộc Tiêu chí loại trừ 6 của Phạm vi §7 — **phải được gắn cờ, không được xóa**. Bản ghi được bảo toàn phục vụ kiểm toán.

> **Thứ tự ưu tiên thực thi giữa §2.2 và §2.4:** Đánh giá §2.2 trước (`null` / chuỗi rỗng). Chỉ thực thi §2.4 khi các trường **tồn tại và có nội dung**, nhưng nội dung ngắn một cách đáng ngờ. Một bản ghi có cả hai trường văn bản đều rỗng thuộc về §2.2 (`INSUFFICIENT_TEXT`), không bao giờ chạm tới §2.4.
>
> Logic xử lý:
> ```python
> if job_description is null/empty and job_requirements is null/empty:
>     → §2.2: INSUFFICIENT_TEXT  # Được kiểm tra trước
> elif len(job_description or "") < 30 and len(job_requirements or "") < 30:
>     → §2.4: SCRAPE_ERROR      # Chỉ kiểm tra khi có văn bản nhưng bị cụt
> ```

| Kịch bản | Điều kiện | Hành động | Cờ lỗi | `relevance_flag` | `exclusion_reason` |
|---|---|---|---|---|---|
| Cả hai trường văn bản đều rỗng/null | Đã xử lý ở §2.2, bỏ qua ở đây | — | — | — | — |
| Cả hai trường văn bản đều có mặt, nhưng đều < 30 ký tự | Các trường có dữ liệu nhưng bị cụt — khả năng lỗi cào dở dang | Giữ lại, gán các cờ | `SCRAPE_FAILED` | `false` | `SCRAPE_ERROR` |
| `source_url` không thể phân tích cú pháp thành URL hợp lệ | Cú pháp URL không hợp lệ | **Loại bỏ** — không thể truy vết/kiểm toán bản ghi | `INVALID_URL` | — | — |
| `raw_job_title` chứa thẻ HTML hoặc chuỗi báo lỗi ("404", "Page not found") | Chức danh phản ánh lỗi HTTP | Giữ lại, gán các cờ | `SCRAPE_ERROR_CONTENT` | `false` | `SCRAPE_ERROR` |

> **Lưu ý:** Các bản ghi có `INVALID_URL` bị loại bỏ vì không thể kiểm toán ngay cả khi được giữ lại. Đây là lỗi kỹ thuật, không phải là việc loại trừ phân tích.

---

## 3. QR-02: Quy tắc Chuẩn hóa Địa điểm (`raw_location` → `normalized_location`)

> Schema §8: `raw_location` phải giữ nguyên bản. Nếu chuẩn hóa được, điền vào `normalized_location`. Tất cả các quy tắc ánh xạ phải được tài liệu hóa trong một bảng tra cứu chuyên dụng ([docs/data_cleaning/location_mapping.csv](docs/data_cleaning/location_mapping.csv)).

### 3.1 Các biến thể quan sát được

Trường `raw_location` thể hiện sự không đồng nhất lớn về định dạng:
- `"Hà Nội"`, `"Ha Noi"`, `"HN"`, `"Hanoi"`, `"TP. Hà Nội"`
- `"Hồ Chí Minh"`, `"HCM"`, `"HCMC"`, `"TP HCM"`, `"TP.HCM"`, `"Ho Chi Minh City"`
- `"Remote"`, `"Work from home"`, `"WFH"`, `"Làm việc từ xa"`
- `"Toàn quốc"`, `"Nationwide"`, `"Cả nước"`
- Đa địa điểm: `"Hà Nội, Hồ Chí Minh"`, `"HN/HCM"`
- Tên chỉ có cấp quận/huyện: `"Quận 7"`, `"Quận 1"`, `"Cầu Giấy"`, `"Thanh Xuân"`
- Chuỗi giữ chỗ: `"Not Available"`, `"Not Available, Not Available"`

### 3.2 Bảng ánh xạ chuẩn hóa (`location_mapping`)

Tóm tắt các mẫu chính:

| Mẫu Regex (Không phân biệt hoa thường) trên `raw_location` | Giá trị `normalized_location` |
|---|---|
| `ha.?noi\|hà.?nội\|\bhn\b` | `Hà Nội` |
| `ho.?chi.?minh\|hồ.?chí.?minh\|\bhcm\b\|hcmc\|tp\.?\s*hcm\|sài.?gòn\|sai.?gon` | `Hồ Chí Minh` |
| `da.?nang\|đà.?nẵng\|\bdn\b` | `Đà Nẵng` |
| `can.?tho\|cần.?thơ` | `Cần Thơ` |
| `hai.?phong\|hải.?phòng` | `Hải Phòng` |
| `binh.?duong\|bình.?dương` | `Bình Dương` |
| `dong.?nai\|đồng.?nai` | `Đồng Nai` |
| Tên quận tại TP.HCM (`quận\s*1\b`, `quận\s*7\b`, `tân\s*bình`, `thủ\s*đức`...) | `Hồ Chí Minh` |
| Tên quận tại Hà Nội (`cầu\s*giấy`, `thanh\s*xuân`, `đống\s*đa`, `ba\s*đình`...) | `Hà Nội` |
| `remote\|wfh\|work.?from.?home\|làm.?việc.?từ.?xa\|online` | `Remote` |
| `toàn.?quốc\|nationwide\|cả.?nước` | `Toàn quốc` |
| Nhiều tỉnh/thành phố (dấu phẩy hoặc `/` giữa các vùng) | `Nhiều địa điểm` |
| Chuỗi giữ chỗ (`not available`, `n/a`, `unknown`) | `null` + cờ `MISSING_LOCATION` |
| Mẫu không nhận diện được | `null` + cờ `LOCATION_UNRECOGNIZED` |

### 3.3 Quy tắc áp dụng

1. Đầu vào: `raw_location` — bất biến, không bao giờ chỉnh sửa tại chỗ.
2. Cắt tỉa khoảng trắng đầu/cuối trước khi khớp mẫu.
3. Nếu `raw_location` chứa cả Hà Nội và TP. Hồ Chí Minh → `normalized_location = "Nhiều địa điểm"`.
4. Nếu `raw_location` chứa tên quận/huyện đã nhận diện → ánh xạ về Tỉnh/Thành phố trực thuộc trung ương tương ứng.
5. Nếu `raw_location` khớp với chuỗi giữ chỗ (ví dụ `'Not Available'`) → `normalized_location = null`, gắn cờ `MISSING_LOCATION`.
6. Nếu không khớp mẫu nào → `normalized_location = null`, gắn cờ `LOCATION_UNRECOGNIZED`.
7. **Không ghi các giá trị nhân tạo** như `"Unknown"` vào `normalized_location`.

---

## 4. QR-03: Quy tắc Chuẩn hóa Kinh nghiệm (`raw_experience` → `experience_min_years` / `experience_max_years`)

> Schema §9: `raw_experience` bảo toàn văn bản thô nguyên bản. `experience_min_years` và `experience_max_years` là các trường số phái sinh. Nếu số năm không thể bóc tách tin cậy, gán `null`. **Tuyệt đối không đưa ra giả định vô căn cứ hoặc ước tính tùy tiện.**

### 4.1 Các biến thể quan sát được

Trường `raw_experience` thể hiện nhiều cách diễn đạt:
- Khoảng: `"1-3 năm"`, `"1 - 3 years"`, `"từ 1 đến 3 năm"`
- Chỉ có cận dưới: `"Trên 2 năm"`, `"Over 2 years"`, `"2+ years"`, `">2 năm"`
- Chỉ có cận trên: `"Dưới 1 năm"`, `"< 1 year"`, `"Fresher"`
- Không xác định / Mở: `"Không yêu cầu"`, `"All levels"`, `"Any"`, `"N/A"`
- Một số nguyên duy nhất: `"3 năm"` (coi min và max bằng nhau)
- Cấp bậc không kèm số năm: `"Senior"`, `"Junior"`, `"Mid-level"`
- Bất thường do crawler: Vô tình bóc tách hình thức làm việc hoặc địa chỉ văn phòng (ví dụ: `"At office"`, `"Hybrid"`, `"174 Thai Ha"`).

### 4.2 Quy tắc bóc tách → `experience_min_years` / `experience_max_years`

> **Phân biệt các giá trị đặc biệt — sử dụng sai sẽ làm lệch phân phối thống kê:**
> - `null` = **Không xác định / Không rõ** (không có dữ liệu hoặc bóc tách thất bại)
> - `-1` trong `experience_max_years` = **Không giới hạn cận trên một cách tường minh** (ví dụ: "2+ years")
>
> Khi tính toán thống kê kinh nghiệm: lọc `IS NOT NULL` trước, sau đó tách riêng `experience_max_years != -1` cho các phép tính cận trên.

| Mẫu trong `raw_experience` | `experience_min_years` | `experience_max_years` | Ghi chú |
|---|---|---|---|
| `"X-Y năm/years"` | X | Y | Khoảng số cụ thể |
| `"Trên X"`, `"X+"`, `">X"`, `"≥X"` | X | -1 | Đã biết tối thiểu X, cận trên mở |
| `"Dưới X"`, `"<X"`, `"≤X"` | 0 | X | Đã biết tối đa X |
| `"X năm/years"` (một số duy nhất) | X | X | Giả định min = max |
| `"Fresher"`, `"0 năm"`, `"Không yêu cầu"` | 0 | 0 | Cấp độ mới vào nghề |
| `"Any"`, `"All levels"`, bị thiếu/null | null | null | Không xác định |
| `"Senior"`, `"Junior"`, `"Mid-level"` | null | null | Lưu ý: Không quy đổi cấp bậc thành số năm. Gắn cờ `EXPERIENCE_LEVEL_ONLY`. Schema §9 nghiêm cấm ước lượng. |
| Chuỗi hình thức làm việc (`"At office"`, `"Hybrid"`...) | null | null | Lỗi lệch trường crawler. Gắn cờ `MISSING_EXPERIENCE` và thông báo cho người phụ trách crawler. |

### 4.3 Quy tắc áp dụng

1. Đầu vào: `raw_experience` — bất biến, không bao giờ chỉnh sửa tại chỗ.
2. Chuẩn hóa văn bản để khớp regex: chuyển chữ thường, bỏ dấu tiếng Việt.
3. Thứ tự ưu tiên: parse khoảng chặn hai đầu (X-Y) trước, tiếp theo là bất đẳng thức một phía (X+, <X), và cuối cùng là số đơn lẻ.
4. Nếu không thể parse được → `experience_min_years = null`, `experience_max_years = null`, gắn cờ `EXPERIENCE_PARSE_FAILED`.
5. Nếu chỉ có cấp bậc seniority → `null`/`null` + gắn cờ `EXPERIENCE_LEVEL_ONLY`.

---

## 5. QR-04: Quy tắc Chuẩn hóa Chức danh (`raw_job_title` → `normalized_job_title`)

> Schema §7: `raw_job_title` phải bảo toàn văn bản gốc. `normalized_job_title` được dùng nghiêm ngặt để loại bỏ nhiễu bề mặt và định dạng — **tuyệt đối không** tự động gộp các vai trò khác nhau (ví dụ: AI Engineer, Machine Learning Engineer, Data Scientist) vào một nhóm chung. Việc gom nhóm ngữ nghĩa thuộc về giai đoạn phân tích nghiên cứu, không thuộc về làm sạch.

### 5.1 Mục tiêu & Ranh giới Phạm vi

Tạo ra `normalized_job_title` như một phiên bản **làm sạch văn bản thuần túy** của `raw_job_title` — loại bỏ các định dạng gây nhiễu — phục vụ cho các mô hình phân tích hạ nguồn. QR-04 **không ánh xạ chức danh sang một taxonomy nghề nghiệp định sẵn**. Việc gom nhóm chức danh thành các cụm nghề nghiệp là mục tiêu nghiên cứu thực nghiệm cốt lõi của RQ1 và RQ4.

### 5.2 Các bước làm sạch văn bản cơ bản

```
Đầu vào:  raw_job_title  (bất biến)
Đầu ra: normalized_job_title (văn bản đã làm sạch, bảo toàn ngữ nghĩa gốc, KHÔNG thay thế nhóm)

1. Cắt tỉa khoảng trắng đầu và cuối chuỗi
2. Chuẩn hóa khoảng trắng nội bộ (gộp nhiều dấu cách liên tiếp thành một dấu cách đơn)
3. Loại bỏ các ký tự đặc biệt vô nghĩa: (), [], số thứ tự danh sách ở đầu, dấu sao (*), dấu thăng (#)
   - Giữ lại: /, +, - khi chúng tạo thành các token kỹ thuật (ví dụ: "C++", "R/Python")
4. Chuyển dạng Title Case: viết hoa chữ cái đầu tiên của mỗi từ
5. Chuẩn hóa các từ viết tắt về mặt định dạng (không làm méo mó ngữ nghĩa):
   - "Sr." → "Senior"
   - "Jr." → "Junior"
   - "Mgr." → "Manager"
   - "Eng." → "Engineer"
   - "Dev." → "Developer"
6. Loại bỏ nhiễu ngoài chức danh: thông tin lương ("Up to 75M"), đãi ngộ ("- BONUS"), dấu câu treo ở cuối ("/")
```

### 5.3 Quy tắc bổ sung

- Nếu tiêu đề chứa rõ ràng hai vai trò riêng biệt (ví dụ: `Data Engineer / Data Analyst`): giữ lại cả hai, gắn cờ `AMBIGUOUS_TITLE` để nhóm phân tích xử lý.
- Nếu tiêu đề quá ngắn (< 3 ký tự sau khi làm sạch): gắn cờ `TITLE_TOO_SHORT`.
- Nếu tiêu đề quá dài (> 100 ký tự): cắt bớt ở 100 ký tự, gắn cờ `TITLE_TOO_LONG`.
- Tuyệt đối không xóa `raw_job_title` gốc.

> **Lưu ý cho Nhóm Phân tích:** Việc ánh xạ `normalized_job_title` sang các nhóm nghề nghiệp được thực hiện hoàn toàn trong giai đoạn phân tích dựa trên phân cụm thực nghiệm — không mã hóa cứng (hard-code) trong pipeline làm sạch.

---

## 6. QR-05: Tiêu chí Phát hiện Bản ghi Trùng lặp (Duplicate Detection Criteria)

> Schema §12: Tuyệt đối không xóa các bản ghi trùng lặp. Sử dụng `duplicate_flag` và `duplicate_group_id` để nhận diện.

### 6.1 Định nghĩa Trùng lặp

**Trùng lặp chính xác (Exact Duplicate):** Hai bản ghi có chung giá trị `source_url`. Bản ghi có `crawl_timestamp` muộn hơn sẽ bị đánh cờ `duplicate_flag = true`.

**Trùng lặp gần (Near Duplicate):** Hai bản ghi có giá trị `source_url` khác nhau nhưng thỏa mãn TẤT CẢ các tiêu chí sau:
- Chung `company` (sau khi trim khoảng trắng và chuyển chữ thường)
- Độ trùng lặp token của `normalized_job_title` $\ge 60\%$ (Jaccard trên word tokens) — cho phép bắt các biến thể Senior/Non-Senior của cùng một vị trí
- Chung `normalized_location`
- Độ tương đồng Cosine của `job_description` $\ge 0.80$ (tính trên biểu diễn bag-of-words hoặc TF-IDF) — **đây là cổng kiểm tra chính**

> **Cơ sở cho việc nới lỏng ràng buộc chức danh:** Việc bắt buộc chức danh *hoàn toàn giống nhau* từng khiến cặp tin của MB Bank (#36 Senior Data Engineer vs #40 Data Engineer) thoát khỏi bộ lọc dù mô tả JD giống nhau đến 88%. Ngưỡng tương đồng `job_description` là tín hiệu quyết định; độ trùng khớp chức danh đóng vai trò là chốt chặn phụ chống dương tính giả.
>
> Nếu các công cụ tính toán tương đồng chưa được nạp: áp dụng heuristic ban đầu — so sánh 200 ký tự đầu tiên của `job_description` sau khi viết thường và xóa khoảng trắng. Hai bản ghi có 200 ký tự đầu tiên giống nhau thuộc cùng một công ty được coi là near-duplicates.
>
> **Chốt chặn Dương tính giả:** Các bản ghi có cấp bậc khác nhau (Senior vs Non-Senior) thỏa mãn ngưỡng JD được gắn cờ `DUPLICATE_NEAR` nhưng đồng thời nhận thêm cờ `SENIORITY_VARIANT` trong `quality_flags`. Các nhà phân tích có thể lựa chọn giữ lại cả hai cho các nghiên cứu dọc về cấp bậc.

### 6.2 Quy trình xử lý

1. **Không xóa** các bản ghi trùng lặp khỏi tập dữ liệu thô.
2. Gán `duplicate_flag = true` cho các bản ghi trùng lặp thứ cấp.
3. Gán `duplicate_group_id` bằng giá trị `job_id` của bản ghi đại diện chuẩn (bản ghi thu thập sớm nhất).
4. Bổ sung `DUPLICATE_EXACT` hoặc `DUPLICATE_NEAR` vào `quality_flags`.
5. Tập dữ liệu phân tích mặc định chỉ giữ lại một bản ghi chuẩn duy nhất cho mỗi nhóm trùng lặp (Schema §12).

### 6.3 Ngưỡng cảnh báo

- Nếu tỷ lệ bản ghi có `duplicate_flag = true` > 15%: **phát cảnh báo**, kiểm tra lại crawler xem có bị trùng lặp đường dẫn thu thập hay không.

---

## 7. QR-06: Tiêu chí Nhận diện Tin không thuộc lĩnh vực Data/AI

> Schema §11: Sử dụng `relevance_flag` (boolean). Khi `relevance_flag = false`, `exclusion_reason` là **bắt buộc** và phải sử dụng các nhãn chuẩn hóa từ một taxonomy định sẵn — không cho phép nhập văn bản tự do tùy tiện.

### 7.1 Mục tiêu

Gắn cờ (không xóa) các tin tuyển dụng nằm ngoài lĩnh vực Data/AI để loại chúng khỏi tập dữ liệu phân tích chính.

QR-06 trực tiếp cài đặt **Tiêu chí Giữ lại (§6)** và **Tiêu chí Loại trừ (§7)** được định nghĩa trong [docs/project_scope.md](docs/project_scope.md).

> **Lưu ý về Phạm vi Thị trường (Scope §5):** Danh sách các chuyên môn trong §5 (Data Analysis, ML, NLP...) đại diện cho ranh giới tìm kiếm của *crawler* — **không phải là một taxonomy nghề nghiệp**. QR-06 không được dùng danh sách này để gán nhãn cứng cho việc làm. Việc phân loại lĩnh vực là kết quả nghiên cứu của RQ1/RQ4.

### 7.2 Bước 1 — Cổng Kiểm tra Danh sách Loại trừ theo Tiêu đề (Title Gate)

**Chạy bước này ĐẦU TIÊN, trước khi Kiểm tra Whitelist.** So khớp `normalized_job_title` với các mẫu loại trừ được định nghĩa ở §7.3.

- Nếu chức danh khớp với nhóm loại trừ tiêu chuẩn → `relevance_flag = false`, `exclusion_reason = "NOT_DATA_AI_ROLE"`. **Dừng — không chạy bước kiểm tra Whitelist.**
- Nếu chức danh khớp với mẫu Nhập liệu (Data Entry) → `relevance_flag = false`, `exclusion_reason = "DATA_ENTRY_ROLE"`. **Dừng.**

> **Cơ sở lý giải:** Việc chạy kiểm tra Whitelist trước bước Loại trừ từng gây ra lỗi dương tính giả: các vai trò như "Advertising Monetization Specialist" (vốn bị loại trừ bởi tiêu đề thuộc nhóm Sales/Marketing) đã bị giữ lại sai do `job_requirements` có chứa các từ khóa kỹ thuật như `SQL` hoặc `API`. Chức danh là tín hiệu chính đáng tin cậy nhất cho phạm vi ngành nghề. Việc quét whitelist trên `job_description`/`job_requirements` chỉ được thực hiện sau khi đã xác nhận tiêu đề không thuộc danh mục bị loại trừ.

### 7.3 Bước 2 — Kiểm tra Từ khóa Data/AI Cốt lõi (Whitelist Check)

Chỉ thực thi nếu bản ghi **chưa** bị loại trừ ở Bước 1. Kiểm tra `raw_job_title` trước, sau đó đến `job_description` và `job_requirements`. Nếu bất kỳ trường nào chứa ít nhất một trong các từ khóa cốt lõi sau → đặt `relevance_flag = true` và kết thúc kiểm tra:

```text
python, r language, sql, spark, hadoop, kafka, airflow, dbt,
pandas, numpy, scikit-learn, tensorflow, pytorch, keras,
machine learning, deep learning, neural network, nlp, llm, gpt,
computer vision, data pipeline, etl, elt, data warehouse, data lake,
power bi, tableau, looker, metabase, superset,
data analyst, data engineer, data scientist, data architect,
bi analyst, analytics engineer, mlops, llmops,
vector database, embedding, rag, fine-tuning,
statistics, regression, classification, clustering, recommendation system
```

> Đối chiếu chéo danh sách này với [taxonomy/skills_taxonomy.csv](taxonomy/skills_taxonomy.csv) của Cường để đảm bảo sự đồng bộ giữa khâu lọc và khâu trích xuất.

### 7.4 Bước 3 — Bảng Tham chiếu Mẫu Danh sách Loại trừ

Bảng này được sử dụng trong Bước 1 (§7.2). Danh sách loại trừ được xây dựng trực tiếp từ **Tiêu chí Loại trừ §7** của [docs/project_scope.md](docs/project_scope.md):

| Danh mục Loại trừ (Nguồn: Scope §7) | Ví dụ Mẫu Regex |
|---|---|
| Thuần IT — không có tác vụ kỹ nghệ hoặc phân tích Data/AI | `software engineer`, `web developer`, `mobile developer`, `devops engineer`, `system admin`, `network engineer`, `qa engineer`, `tester`, `sap specialist`, `sap mm`, `sap fico` |
| Bán hàng / Marketing cho các sản phẩm AI hoặc Công nghệ | `sales`, `marketing`, `business development`, `account manager`, `hr`, `recruiter`, `monetization specialist` |
| Nhập liệu — thao tác nhập văn phòng không có phân tích | `data entry`, `data input`, `nhập liệu` |
| Vận hành / Tài chính / Kế toán | `accountant`, `finance`, `logistics`, `supply chain`, `operations` |
| Thiết kế UI/UX & Đồ họa | `ui/ux designer`, `graphic designer` |
| Quản lý chung / Học bổng (phi kỹ thuật) | `general manager`, `project manager`, `scholarship` |

> **Thực tập sinh / Mới tốt nghiệp:** Scope §6 giữ lại thực tập sinh/fresher nếu vai trò *thực sự* mang tính kỹ thuật Data/AI. Không lọc ứng viên chỉ dựa trên cấp bậc — phải đánh giá nội dung công việc.
>
> **Chức danh mơ hồ:** Khi một chức danh vừa chứa token Data/AI *vừa* chứa token loại trừ (ví dụ: "AI Sales Manager"), mẫu loại trừ sẽ được ưu tiên áp dụng trước. Bản ghi được gắn cờ `NOT_DATA_AI_ROLE` kèm theo ghi chú phụ `AMBIGUOUS_CLASSIFICATION` trong `quality_flags` phục vụ rà soát thủ công.

### 7.5 Bước 4 — Kiểm thực Văn bản Bị cắt cụt (Truncated Text)

- Nếu `job_description` < 50 ký tự sau khi trim → gán cờ `DESCRIPTION_TOO_SHORT`, chuyển sang rà soát thủ công.

### 7.6 Taxonomy Chuẩn hóa của `exclusion_reason`

Schema §11 bắt buộc sử dụng các nhãn chuẩn hóa. Tập từ vựng được trích xuất từ Tiêu chí Loại trừ của Scope §7:

| Nhãn (Label) | Định nghĩa | Căn cứ Scope §7 | Gán bởi |
|---|---|---|---|
| `NOT_DATA_AI_ROLE` | Chức danh xác nhận vai trò nằm ngoài phạm vi Data/AI | §7 tiêu chí 1, 3, 4 | QR-06 Bước 1 |
| `DATA_ENTRY_ROLE` | Vai trò thuần nhập liệu — thiếu tác vụ phân tích hoặc kỹ nghệ | §7 tiêu chí 2 | QR-06 Bước 1 |
| `INSUFFICIENT_TEXT` | Thiếu cả hai trường văn bản — không đủ dữ liệu đánh giá tính liên quan | §7 tiêu chí 5 | QR-01 §2.2 |
| `SCRAPE_ERROR` | Trang lỗi, link hỏng hoặc nội dung cào bị hỏng | §7 tiêu chí 6 | QR-01 §2.4 |
| `MANUAL_REVIEW_REQUIRED` | Vai trò chưa nhận diện được không khớp whitelist lẫn exclusion list — giữ lại rà soát thủ công | — | QR-06 Bước 3 |

### 7.7 Các quy tắc trong Luồng Quyết định

1. **Bước 1 — Cổng Chức danh Loại trừ (§7.2):**
   - Nếu chức danh khớp nhóm loại trừ chuẩn → `relevance_flag = false`, `exclusion_reason = "NOT_DATA_AI_ROLE"`. **Dừng.**
   - Nếu chức danh khớp mẫu Nhập liệu → `relevance_flag = false`, `exclusion_reason = "DATA_ENTRY_ROLE"`. **Dừng.**
2. **Bước 2 — Kiểm tra Whitelist (§7.3):** Nếu chức danh không bị loại ở Bước 1 → quét `raw_job_title`, `job_description`, `job_requirements` tìm từ khóa whitelist. Nếu khớp bất kỳ từ khóa nào → `relevance_flag = true`. **Dừng.**
3. **[Mặc định tường minh]** Nếu không khớp danh sách nào → `relevance_flag = true`, thêm `MANUAL_REVIEW_REQUIRED` vào `quality_flags` — mặc định giữ lại phục vụ con người kiểm toán.
4. **Bước 4 — Kiểm tra Chất lượng Văn bản (§7.5):** Nếu `job_description` < 50 ký tự → thêm cờ `DESCRIPTION_TOO_SHORT`; nếu cả hai trường văn bản < 50 ký tự → gán `exclusion_reason = "INSUFFICIENT_TEXT"`.
5. Không bao giờ xóa bản ghi.
6. Tập dữ liệu phân tích mặc định lọc `relevance_flag = true` và `duplicate_flag = false`.

> **Đã kiểm chứng trên dữ liệu mẫu:** Bản ghi #11 "Advertising Monetization Specialist" — trước đây là một ca dương tính giả dưới luồng cũ (whitelist chạy trước, `SQL` trong requirements khiến `relevance_flag = true`). Dưới luồng đã sửa, Bước 1 khớp `monetization specialist` trong nhóm loại trừ Sales/Marketing và gán `relevance_flag = false, exclusion_reason = "NOT_DATA_AI_ROLE"` trước khi chạm tới bước quét whitelist.

---

## 8. Ghi chú về các Vấn đề Phát hiện từ 30–50 Tin Tuyển dụng Mẫu

| STT | Vấn đề Thực nghiệm Quan sát được | Tỷ lệ Bị ảnh hưởng | Các trường Bị ảnh hưởng | Đánh giá & Cách Xử lý dựa trên Quy tắc |
|---|---|---|---|---|
| 1 | **Lệch trường Kinh nghiệm của Crawler:** Crawler map nhầm hình thức làm việc và địa chỉ văn phòng vào `raw_experience` thay vì số năm kinh nghiệm. Chi tiết (khớp chuỗi con): `At office`: 33 bản ghi (chính xác); `Hybrid`: 5 bản ghi (3 chính xác + 2 phức hợp `"Hybrid, [địa chỉ]"`); `Remote`: 2 bản ghi (1 chính xác + 1 phức hợp `"Remote, Da Nang"`); chỉ có địa chỉ văn phòng: 5 bản ghi (#09, #10, #20, #28, #45). | 45/45 bản ghi (100.0%) | `raw_experience` | **Yêu cầu Đạt sửa crawler.** QR-03 không thể parse số năm kinh nghiệm từ trường này cho đến khi crawler được vá; số năm kinh nghiệm tạm thời phải bóc tách từ `job_requirements`. |
| 2 | **Địa điểm Thiếu Tỉnh/Thành phố & Có chuỗi Giữ chỗ:** 20 bản ghi chứa chuỗi `'Not Available'` tại bất kỳ vị trí nào (44.4%); 8 bản ghi là chuỗi đa địa điểm chứa dấu phẩy (ví dụ: `'Quận 1, Quận Đống Đa'`, `'Quận Phú Nhuận, Not Available'`); 21 bản ghi chỉ chứa tên quận/huyện (`Quận 1`, `Quận 7`, `Thanh Xuân`, `Cầu Giấy`, `Tây Hồ`, `Nam Từ Liêm`, `Thành phố Thủ Đức`...) mà không có tên thành phố. Lưu ý: các nhóm này có sự giao thoa lẫn nhau. | 45/45 bản ghi (100.0%) | `raw_location` | Áp dụng QR-02: chuyển thành phần `'Not Available'` thành `null` với cờ `MISSING_LOCATION`. Ánh xạ tên quận huyện về Tỉnh/Thành phố qua `location_mapping.csv`. Các tin đa địa điểm ánh xạ thành `'Nhiều địa điểm'`. |
| 3 | **Nhiễu Định dạng Chức danh:** Tiêu đề dính mức lương (`Up to 75M`), đãi ngộ (`- BONUS`), dấu câu treo ở đuôi (`English required, /`), lỗi chính tả (`Appllication/Intergration`), và 34/45 tiêu đề bị nối dính từ khóa kỹ năng công nghệ. | 38/45 bản ghi (84.4%) | `raw_job_title` | Áp dụng QR-04: thực hiện làm sạch bề mặt, loại bỏ nhiễu lương/thưởng/dấu câu thừa, chuẩn hóa chữ hoa thường sang `normalized_job_title`. Văn bản gốc được giữ nguyên trong `raw_job_title`. |
| 4 | **Tin Tuyển dụng Nằm ngoài Phạm vi:** 4 bản ghi thuộc vai trò ERP (`Senior SAP Specialist`), chương trình học bổng chung (`VPBank Scholarship`), vận hành quảng cáo (`Ad Monetization Specialist`), và kiểm thử phần mềm (`Internship BA/QA`). | 4/45 bản ghi (8.9%) | `raw_job_title`, `job_description` | Áp dụng QR-06: loại khỏi tập phân tích chính bằng cách gán `relevance_flag = false`, `exclusion_reason = "NOT_DATA_AI_ROLE"`. |
| 5 | **Tin Tuyển dụng Trùng lặp Gần — Đã Kiểm chứng Thực nghiệm:** Tính toán qua TF-IDF cosine (JD) và Jaccard (token chức danh) trực tiếp từ dữ liệu. **Cặp tin xác nhận:** #36 `"Senior AI Expert Machine Learning, Deep Learning, LLM"` so với #40 `"AI Expert Computer Vision/NLP/LLM"` (đều của MB Bank) — Title Jaccard = 0.30 (dưới ngưỡng 60%), JD TF-IDF cosine = 0.988 (vượt xa ngưỡng 80%). **Chưa bị bắt bởi QR-05** vì logic AND đòi hỏi cả 2 điều kiện — đây là trường hợp biên đã gắn cờ báo cáo Leader. **Cặp tin loại trừ đúng (False positive):** #27 `"Snr/Lead Data Engineer Pyspark, Snowflake - BONUS"` so với #33 `"Snr/Lead Data Software Engineer Pyspark, Snowflake"` (đều của EPAM Vietnam) — Title Jaccard = 0.75 (trên 60%), JD cosine = 0.51 (dưới 80%). Cổng JD loại bỏ chính xác cặp này — hai bản mô tả vai trò hoàn toàn khác nhau dưới tiêu đề tương tự. | 4/45 bản ghi (8.9%) | `company`, `job_description` | **Đối với cặp MB Bank:** Logic AND của QR-05b không bắt được dưới ngưỡng hiện tại (Jaccard tiêu đề 0.30 < 60%). Đề xuất Leader cho phép sử dụng riêng Cosine của JD như một cổng đủ điều kiện khi cosine $\ge 0.95$ — điều này sẽ bắt được cặp #36/#40 mà không tăng rủi ro dương tính giả. **Đối với cặp EPAM:** Không cần can thiệp; cổng JD đã loại trừ đúng. |
| 6 | **Thiếu các trường Lương và Học vấn:** 100% bản ghi thiếu `salary_raw` và `education` do ITviec ẩn lương sau màn hình đăng nhập và không có phần tử học vấn độc lập trên giao diện. | 45/45 bản ghi (100.0%) | `salary_raw`, `education` | Áp dụng QR-01: gán `null`, tránh dùng giá trị nhân tạo theo chuẩn bất biến của Schema §2 và §10. |

> **Ghi chú gửi Leader — Giới hạn Logic AND của QR-05:** Cặp tin MB Bank (#36 Senior AI Expert ML/DL/LLM so với #40 AI Expert CV/NLP/LLM) có JD cosine = 0.988 nhưng Jaccard tiêu đề = 0.30. Dưới logic AND hiện tại (tiêu đề $\ge 60\%$ VÀ JD $\ge 0.80$), cặp này không bị đánh cờ. Đây gần như chắc chắn là cùng một template việc làm được đăng dưới các chuyên ngành khác nhau. Điều chỉnh đề xuất: đưa vào luồng ưu tiên độ tin cậy cao dựa trên JD — nếu JD cosine $\ge 0.95$ VÀ cùng công ty → gán cờ `DUPLICATE_NEAR` + `SENIORITY_VARIANT` bất kể độ trùng khớp tiêu đề. Điều này vừa giữ an toàn cho các cặp có độ tương đồng thấp vừa bắt được các template JD gần như giống hệt nhau.
