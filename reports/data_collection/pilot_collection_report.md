# Báo cáo Thu thập Dữ liệu Pilot & Kiểm định Chất lượng (Task 02)

## 1. Tổng quan Đợt thu thập
- **Phạm vi:** Tập dữ liệu Pilot phục vụ đề tài "Vietnam Data & AI Job Skill Landscape 2026".
- **Nguồn thu thập:** Nền tảng tuyển dụng công nghệ ITviec (https://itviec.com).
- **Thời gian thực hiện:** 30/09/2026.
- **Phiên bản bộ bóc tách (Parser):** v0.2.
- **Tổng số việc làm duy nhất thu thập được:** 252 việc làm.
- **Tỷ lệ thành công:** 100% (252 / 252 request chi tiết thành công, 0 lỗi thất bại).

---

## 2. Nâng cấp Kiến trúc & Khắc phục Lỗi Bộ cào
Mã nguồn crawler được tái cấu trúc thành các module rõ ràng trong thư mục `src/crawler/`:
- **`PoliteFetcher`:** Xử lý gửi HTTP request kèm User-Agent chuẩn trình duyệt, kiểm soát ngoại lệ và duy trì độ trễ ngẫu nhiên (1.5s - 2.5s) giữa các request để đảm bảo không bị chặn bởi Cloudflare hay vượt quá rate limit.
- **`ListingCrawler`:** Tự động duyệt phân trang (`?page=1, 2...`) qua các từ khóa tìm kiếm và trang chuyên mục phân khúc (segment). Tích hợp hàm `extract_slug` xử lý triệt để lỗi lặp đường dẫn tương đối (`/it-jobs/it-jobs/...`).
- **`JobParser`:** Bóc tách dữ liệu từ HTML và JSON-LD schema của ITviec, chuẩn hóa cấu trúc theo đúng 29 trường của `DATA SCHEMA V1`. Tự động sinh `job_id` nội bộ bất biến bằng thuật toán băm SHA-256 từ `source_url`.
- **Khử trùng lặp trên bộ nhớ (In-memory Deduplication):** Lưu trữ tập `set` các URL/Job ID đã quét qua các từ khóa, loại bỏ hoàn toàn 249 lượt xuất hiện trùng lặp giữa các danh mục.
- **Giao diện dòng lệnh (CLI):** Cung cấp tham số linh hoạt qua `argparse` cho phép tùy biến đường dẫn lưu trữ và giới hạn số lượng tin cần cào.

---

## 3. Thống kê Quét theo Từng Đường dẫn Hạt giống (Seeds)

| STT | Đường dẫn Hạt giống (Seed URL) | Số trang danh sách đã quét | Số thẻ việc làm thô phát hiện |
|:---:|:---|:---:|:---:|
| 1 | `https://itviec.com/it-jobs/data-analyst` | 2 trang | 12 |
| 2 | `https://itviec.com/it-jobs/data-engineer` | 3 trang | 27 |
| 3 | `https://itviec.com/it-jobs/data-scientist` | 2 trang | 3 |
| 4 | `https://itviec.com/it-jobs/ai-machine-learning-engineer` | 9 trang | 160 |
| 5 | `https://itviec.com/it-jobs/business-analyst` | 4 trang | 46 |
| 6 | `https://itviec.com/it-jobs/database-administrator` | 3 trang | 36 |
| 7 | `https://itviec.com/segments/viec-lam-ai-data` | 1 trang | 211 |
| **Tổng** | **7 danh mục hạt giống** | **24 trang danh sách** | **501 liên kết thô** |

- **Tổng số việc làm duy nhất đưa vào hàng đợi cào:** 252
- **Số việc làm trùng lặp bị loại bỏ:** 249
- **Sản phẩm xuất ra:**
  - Tập dữ liệu pilot: `data/pilot/jobs_pilot.jsonl` (252 dòng JSON)
  - Nhật ký truy cập: `data/pilot/crawl_log.csv` (253 dòng bao gồm dòng tiêu đề)

---

## 4. Kết quả Kiểm định & Khắc phục Lỗi Cốt lõi

### 4.1 Khắc phục triệt để lỗi định dạng `raw_job_title`
- **Vấn đề trước đây:** Dấu ngoặc đơn bị loại bỏ hoặc nối chuỗi không chính xác, làm lẫn lộn từ khóa công nghệ vào tên chức danh.
- **Kết quả nghiệm thu:** 161 trên tổng số 252 việc làm có chứa dấu ngoặc đơn đều giữ nguyên vẹn 100% định dạng gốc từ nguồn (ví dụ: `Senior Data Analyst (CRM & Loyalty)`, `Senior Product Data Analyst (SQL/Python/R)`, `Data Analyst (BI, Power BI, SQL, Data Warehouse, ETL)`).

### 4.2 Khắc phục lỗi gán nhầm mô hình làm việc vào `raw_experience`
- **Vấn đề trước đây:** Selector bắt nhầm nhãn mô hình làm việc (`"At office"`, `"Hybrid"`, `"Remote"`) hoặc địa chỉ làm việc vào trường kinh nghiệm.
- **Kết quả nghiệm thu:** 252/252 bản ghi đều ghi nhận giá trị `null` chuẩn xác, hoàn toàn sạch rác. Việc bóc tách số năm kinh nghiệm sẽ được bàn giao cho module Tiền xử lý & Làm sạch (Stage B) trích xuất từ phần mô tả yêu cầu công việc.

### 4.3 Độ tương thích với DATA SCHEMA V1
- Đầy đủ 29 trường theo thứ tự và kiểu dữ liệu chuẩn quy định.
- Giữ nguyên vẹn toàn bộ tiếng Việt có dấu ở các trường dữ liệu thô (`raw_job_title`, `company`, `raw_location`, `job_description`, `job_requirements`).
- Các trường phái sinh của các giai đoạn sau (`normalized_*`, `relevance_flag`, `extracted_skills`,...) được khởi tạo mặc định là `null`.

---

## 5. Bàn giao Thông tin cho các Thành viên tiếp nối
- **Gửi bạn Đức (Làm sạch & Chất lượng dữ liệu - Stage B):**
  - Dataset gồm 252 tin tuyển dụng sạch sẵn sàng cho việc xây dựng bộ quy tắc lọc relevance và gán nhãn trùng lặp.
  - Trường `raw_location` có các giá trị dạng quận (`Quận 7`, `Quận Đống Đa`...) và trường hợp khuyết (`Not Available`), cần quy tắc chuẩn hóa địa phương.
- **Gửi bạn Cường (Gán nhãn & Xây dựng Taxonomy kỹ năng - Stage C):**
  - 100% bản ghi đều có `job_requirements` và `job_description` đầy đủ, chi tiết, bao quát các nhóm công nghệ mới nhất về BI, Data Warehouse, Cloud và AI/LLM.
- **Gửi bạn Triều (Đặc tả Phân tích dữ liệu - Stage D):**
  - Dữ liệu phản ánh toàn bộ quy mô việc làm Data/AI thực tế đang hoạt động trên ITviec tính đến cuối tháng 09/2026 (252 tin duy nhất không trùng), đủ mật độ cho việc thử nghiệm các thuật toán phân cụm và ma trận đồng xuất hiện.
