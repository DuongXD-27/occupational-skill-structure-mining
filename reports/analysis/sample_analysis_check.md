# BÁO CÁO KIỂM TRA DỮ LIỆU MẪU CHO PHÂN TÍCH (SAMPLE ANALYSIS CHECK)

**Người phụ trách:** Hồ Nhật Triều (20236003) · **Ngày thực hiện:** 2026-09-24

**Tập dữ liệu:** `data/sample/sample_jobs.jsonl` — 45 tin tuyển dụng, nguồn ITviec, parser_version: "v0.1", thời gian đăng từ 2026-08-13 đến 2026-09-15

**Câu hỏi cốt lõi:** chúng ta đã có thể chạy các phân tích trong [docs/analysis/analysis_spec.md](docs/analysis/analysis_spec.md) trên tập dữ liệu này hay chưa?

---
---

# 1. KẾT LUẬN CHUNG (VERDICT)

| Phép phân tích | Có thể chạy chưa? | Lý do nếu chưa |
|---|---|---|
| **RQ1** — đếm số lượng chức danh | Chỉ chạy thử nghiệm pipeline | — |
| **RQ1** — đo mức độ phân mảnh chức danh | **Chưa** | Chức danh bị crawler thu thập sai định dạng |
| **RQ1** — phân bổ theo địa điểm | **Chưa** | 24/45 địa điểm không thể sử dụng trực tiếp |
| **RQ2** — kỹ năng nào phổ biến | **Chưa** | Kỹ năng chưa được trích xuất |
| **RQ2** — kỹ năng nào đi cùng nhau | **Chưa** | Kỹ năng chưa trích xuất, và quá ít tin tuyển dụng |
| **RQ3** — cùng chức danh, khác kỹ năng | **Chưa** | **Không có chức danh nào đạt 5 tin**, và chưa có kỹ năng |
| **RQ3** — khác chức danh, cùng kỹ năng | **Chưa** | Kỹ năng chưa được trích xuất |
| **RQ4** — thuật toán tự gom nhóm việc làm | **Chưa** | Mới có 45 tin, chúng ta cần tối thiểu 300 tin |
| **RQ4** — biểu đồ PCA | **Chưa** | Biểu đồ này vẽ kết quả của RQ4, mà RQ4 chưa có kết quả |

## Ba nguyên nhân chính

**Một lỗi kỹ thuật thực tế:** Chức danh công việc bị lưu trữ sai cách. Lỗi này thuộc trách nhiệm nhóm chúng ta phải sửa — xem mục 2. Đây là một trong hai yếu tố gây nghẽn trực tiếp RQ3.

**Đang chờ bộ trích xuất:** Kỹ năng chưa được bóc tách từ văn bản, nên mọi phân tích cần dữ liệu kỹ năng đều không thể chạy — bao gồm RQ2 và **cả hai chiều của RQ3**.

**Đang chờ quy mô dữ liệu:** RQ4 cần tối thiểu khoảng 300 tin tuyển dụng. Hiện tại chúng ta mới có 45 tin.

Hiện tại, chỉ có nguyên nhân thứ nhất là cần hành động khắc phục ngay lập tức.

---
---

# 2. RQ1 — NHỮNG CHỨC DANH CÔNG VIỆC NÀO TỒN TẠI

**Các trường cần dùng:** `raw_job_title`, `normalized_job_title`, `raw_location`

## Các con số thực tế

| Tiêu chí | Số lượng |
|---|---|
| Tổng số tin tuyển dụng | 45 |
| Số lượng chức danh công việc khác biệt | **45** |
| Số lượng chức danh sau khi dọn dẹp cơ bản | 43 |
| Số chức danh chỉ xuất hiện đúng một lần | 42 trên 43 |
| Nhóm chức danh giống nhau lớn nhất | 3 |
| Chức danh bị dính danh sách công nghệ bên trong | **19** |
| `normalized_job_title` đã được điền | 0 trên 45 |

45 tin tuyển dụng tạo ra 45 chức danh hoàn toàn khác nhau. Không có chức danh nào lặp lại đáng kể.

## Nguyên nhân: chức danh đang bị bóc tách sai

Trên giao diện ITviec, chức danh hiển thị dạng:

```text
Data Analyst (Azure, SQL, NoSQL, Power BI)
```

Crawler lại lưu vào dữ liệu như sau:

```text
Data Analyst Azure, SQL, NoSQL, Power BI
```

Dấu ngoặc đơn bị rớt mất, do đó danh sách các công nghệ bị nối liền vào tên công việc. **19 trên tổng số 45 tin bị ảnh hưởng bởi lỗi này.**

Điều đó có nghĩa là `Data Engineer` và `Data Engineer Java, Python, SQL` bị đếm thành hai công việc hoàn toàn khác nhau, trong khi bản chất chúng là cùng một nghề nghiệp được quảng bá với các công cụ cụ thể.

Ba trường hợp lỗi tiêu biểu nhất:

| Chức danh đang lưu | Lỗi phát sinh |
|---|---|
| `Data Engineer English required, /` | Bị hỏng — tiêu đề bị cắt cụt và để lại dấu gạch chéo phân cách |
| `Data Engineer Good English - Up to 75M` | Mức lương bị lọt vào bên trong tên công việc |
| `Senior Data Engineer Databricks, SQL, Python, ETL/ELT` | Bốn công nghệ bị nối dính vào tên công việc |

**Vì vậy, bất kỳ con số nào chúng ta công bố về "mức độ phân mảnh chức danh" đều sẽ bị thổi phồng quá cao, và sai lệch đó xuất phát từ crawler của chúng ta chứ không phải từ thị trường.** Chúng ta không được phép báo cáo chỉ số này cho đến khi chức danh được sửa lại.

## Địa điểm (Location)

| Tình trạng địa điểm | Số lượng |
|---|---|
| Sử dụng được (một quận/huyện rõ ràng) | 21 |
| Giá trị giữ chỗ `"Not Available"` | 20 |
| Hai giá trị trong cùng một trường (`"Quận 1, Quận khác"`) | 8 |

Ngoài ra, các giá trị này mới ở cấp quận/huyện. RQ1 cần phân bổ theo cấp Tỉnh/Thành phố, nên vẫn cần bước quy đổi. Hiện tại `normalized_location` đang để trống trên cả 45 tin.

---
---

# 3. RQ2 — NHỮNG KỸ NĂNG NÀO ĐƯỢC YÊU CẦU NHIỀU NHẤT

**Trường cần dùng:** `extracted_skills`

Cả `extracted_skills` và `skill_count` đều đang trống (`null`) trên toàn bộ 45 tin tuyển dụng. Bộ trích xuất kỹ năng chưa được xây dựng, vì vậy **chưa thể kiểm tra bất kỳ phân tích nào trong RQ2.**

## Những gì đã sẵn sàng

`job_description` và `job_requirements` đã được điền đầy đủ 100% trên cả 45 tin, và được tách thành hai trường riêng biệt. Đây chính xác là những gì bộ trích xuất cần để đọc, và chất lượng văn bản hiện rất tốt.

## Hai điểm chúng ta vẫn chưa thể kiểm tra

Cả hai yếu tố này quyết định việc kết quả RQ3 có đáng tin cậy hay không, và cả hai đều đòi hỏi phải có bộ trích xuất trước:

- **Độ bao phủ (Coverage)** — có bao nhiêu tin tuyển dụng cuối cùng không trích xuất được kỹ năng nào. Mục tiêu: dưới 10%.
- **Độ sâu (Depth)** — một tin tuyển dụng thông thường trích xuất được bao nhiêu kỹ năng. Mục tiêu: trung bình ít nhất 3 kỹ năng.

Nếu bộ trích xuất chỉ tìm được 1–2 kỹ năng trên mỗi tin, mọi tin tuyển dụng sẽ trông hoàn toàn khác nhau, và RQ3 sẽ tạo ra một kết luận giật gân sai lệch vì lỗi kỹ thuật.

---
---

# 4. RQ3 — CHỨC DANH CÔNG VIỆC CÓ KHỚP VỚI KỸ NĂNG KHÔNG

**Yêu cầu:** các nhóm có ít nhất 5 tin tuyển dụng dùng chung chức danh, cộng với dữ liệu kỹ năng đã trích xuất

| Tiêu chí | Thực tế hiện tại |
|---|---|
| Số chức danh có từ 5 tin trở lên | **0** |
| Nhóm lớn nhất | 3 tin (`data engineer`) |
| Kỹ năng đã trích xuất | Chưa có |

Cả hai nửa phân tích của RQ3 đều đang bị tắc nghẽn. So sánh các tin trong cùng một chức danh đòi hỏi một nhóm tin — hiện tại không có. So sánh chức danh này với chức danh khác đòi hỏi có các nhóm để so sánh — hiện tại cũng không có.

## Thị trường không phân mảnh đến mức này — crawler của chúng ta làm nó phân mảnh

Nếu dấu ngoặc đơn được giữ nguyên, 45 tin tuyển dụng này sẽ tự động gom nhóm lại như sau:

| Nhóm nghề nghiệp tự nhiên | Số tin tuyển dụng |
|---|---|
| **Data Engineer** | **19** |
| **Data Analyst** | **8** |
| **AI Engineer** | **7** |
| ML Engineer | 2 |
| AI Expert / Lead | 2 |
| Data Manager / Leader | 2 |
| Các vai trò khác (bao gồm 5 tin ngoài phạm vi) | 5 |

**Có 3 nhóm nghề nghiệp đạt trên 5 tin tuyển dụng.**

## Bài học rút ra

**RQ3 cần hai điều kiện, và cả hai hiện đều đang thiếu:** các nhóm có tối thiểu 5 tin dùng chung chức danh, và các kỹ năng đã trích xuất để so sánh bên trong các nhóm đó. Việc gom nhóm thủ công ở trên chứng minh rằng điều kiện thứ nhất hoàn toàn có thể khắc phục được ngay lập tức ở phía chúng ta. Điều kiện thứ hai đang chờ bộ trích xuất.

**Việc sửa crawler vào lúc này mang lại giá trị cao hơn nhiều so với việc cố thu thập thêm 45 tin nữa.** Cào tiếp mà không sửa lỗi sẽ chỉ tạo thêm 45 chức danh không thể sử dụng.

Bảng gom nhóm ở trên được thực hiện thủ công để chỉ rõ nguồn gốc lỗi. Đây không phải là quy tắc chuẩn hóa chức danh đề xuất — đó là công việc thuộc giai đoạn làm sạch của Đức.

---
---

# 5. RQ4 — ĐỂ THUẬT TOÁN TỰ GOM NHÓM VIỆC LÀM

**Yêu cầu:** kỹ năng đã trích xuất cho ít nhất 300 tin tuyển dụng

Hiện tại chúng ta có 45 tin và chưa có kỹ năng nào.

Với khoảng 100–200 kỹ năng tiềm năng và kỳ vọng tìm ra 5–10 cụm, 45 tin là quá ít. Bất kỳ phân cụm nào mà thuật toán tìm ra đều chỉ là do ngẫu nhiên, và sẽ thay đổi mỗi khi chúng ta chạy lại trên một mẫu dữ liệu hơi khác.

Biểu đồ PCA không phải là một vấn đề tách rời — nó trực quan hóa kết quả của RQ4, mà hiện tại chưa có kết quả nào để vẽ.

Phân tích này tạm thời hoãn lại cho đến khi quy mô thu thập đạt mốc 1.000–2.500 tin như mục tiêu của phạm vi dự án.

---
---

# 6. THỰC TẾ CHÚNG TA ĐANG CÓ BAO NHIÊU TIN HỢP LỆ

Có 5 tin tuyển dụng hoàn toàn nằm ngoài phạm vi đề tài, và `relevance_flag` chưa được gán trên bất kỳ tin nào:

| job_id | Chức danh công việc | Lý do không thuộc phạm vi |
|---|---|---|
| `75437956e1aaafed` | Intern Job Future VPBanker Scholarship 2026 | Chương trình học bổng, không phải việc làm |
| `f2c6a7172480656b` | Advertising Monetization Specialist | Vận hành quảng cáo (AdOps) |
| `691b9cac78b7c50d` | Internship - BA | Thực tập sinh Business Analyst phi kỹ thuật |
| `82f0c2527791a6f5` | Senior SAP Speicialist SAP MM, SD, FICO | Chuyên viên tư vấn ERP SAP |
| `360018923611096a` | AI Automation Engineer Senior/Lead | Người sử dụng công cụ AI; không phải người xây dựng AI |

**Số lượng tin tuyển dụng thực sự có thể sử dụng là 40, không phải 45.**

Mọi số liệu trong báo cáo này tạm thời tính trên 45. Khi cờ liên quan được gán chính thức, giai đoạn phân tích sẽ chỉ thực thi trên 40 tin.

Ngoài ra có 3 tin ở vùng ranh giới nhạy cảm cần Trưởng nhóm (Leader) quyết định:

- `f42ffe22ea73beff` — vai trò QA kiểm thử các hệ thống AI
- `752e8906a23eb6e9` — một tin tuyển dụng đăng gộp hai công việc khác nhau
- `1a00e9575f25cfb1` — chính tin tuyển dụng ghi rõ: 70% việc dữ liệu, 30% vận hành và marketing

---
---

# 7. NHỮNG ĐIỂM CẦN KHẮC PHỤC

## Khâu Thu thập dữ liệu — Đạt

1. **Giữ nguyên dấu ngoặc đơn khi bóc tách chức danh công việc.** Đây là điểm sửa duy nhất giúp khai thông ngay một phép phân tích. Nếu lưu phần nội dung trong ngoặc ra một trường riêng biệt thì càng tốt hơn.
2. **Kiểm tra tin `Data Engineer English required, /`** — tiêu đề bị cắt cụt lỗi.
3. **Địa điểm bị thiếu ở 20/45 tin.** Cần quy định cách xử lý khi một tin liệt kê 2 địa điểm: lưu một bản ghi chứa cả hai hay tách thành hai bản ghi.
4. **Trường kinh nghiệm đang trỏ nhầm phần tử trên trang.** Cả 45 tin đều có dữ liệu nhưng không có tin nào chứa số năm kinh nghiệm — 37 tin chứa hình thức làm việc (`At office`, `Hybrid`, `Remote`) và 8 tin chứa địa chỉ đường phố. Phân tích hiện tại chưa dùng đến kinh nghiệm nên không quá khẩn cấp, nhưng lỗi này sẽ trở nên khó kiểm soát khi có 2.000 tin. Kinh nghiệm thực tế nằm trong trường `job_requirements`.

## Khâu Làm sạch dữ liệu — Đức

5. **Chuẩn hóa chức danh công việc là đường găng quan trọng nhất (Critical Path).** Các quy tắc cần loại bỏ cả từ chỉ cấp bậc lẫn danh sách công nghệ đi kèm. 26/45 tiêu đề có chứa từ chỉ cấp bậc seniority.
6. **Địa điểm** — chuyển đổi cấp quận/huyện thành Tỉnh/Thành phố, và chuyển `"Not Available"` thành `Unknown` thay vì để trống.
7. **Gán cờ `relevance_flag` và `exclusion_reason`.** Phạm vi dự án mục 7 quy định rõ các tin bị loại phải được giữ lại và đánh dấu lý do, không được xóa.
8. **Khi bộ trích xuất không tìm thấy kỹ năng, hãy ghi một danh sách rỗng `[]`, không để null.** Null mang nghĩa bộ trích xuất chưa từng chạy, đó là hai vấn đề kỹ thuật khác nhau.
9. **Không khử trùng lặp dựa trên chức danh.** Cùng một công việc có thể xuất hiện dưới các chức danh khác nhau trên các trang khác nhau. Hãy so sánh mô tả công việc, hoặc dùng mã tuyển dụng riêng của doanh nghiệp — ví dụ nhiều tin của MB Bank bắt đầu bằng mã như `2026TD450985`.

---
---

# 8. KẾT LUẬN

**Chưa sẵn sàng. Có hai yếu tố gây nghẽn RQ3, và chỉ có một yếu tố là thuộc trách nhiệm chúng ta có thể sửa ngay.**

Cấu trúc dữ liệu đã chuẩn hóa tốt và mọi trường thuộc trách nhiệm thu thập đều đã có dữ liệu. Mô tả và yêu cầu công việc đầy đủ và được phân tách chính xác. **Bước trích xuất kỹ năng chưa được xây dựng, do đó pipeline chưa thể chạy từ đầu đến cuối.**

**Điểm nghẽn có thể sửa ngay:** danh sách công nghệ bị nối dính vào chức danh công việc (19/45 tin). Đây là lý do không chức danh nào đạt ngưỡng 5 tin.

**Điểm nghẽn phụ thuộc module khác:** `extracted_skills` đang null trên cả 45 tin. RQ2 và cả hai chiều của RQ3 đều cần trường này. RQ4 cần bổ sung thêm khoảng 300 tin.

Việc sửa tiêu đề chưa khai thông toàn bộ RQ3 ngay lập tức — nó chỉ gỡ bỏ một trong hai chốt chặn.

**Bước tiếp theo:** chạy lại bài kiểm tra này sau khi chức danh đã được sửa và sau khi kỹ năng đã được trích xuất. Khi đó các số liệu đếm của RQ1 và tần suất kỹ năng của RQ2 sẽ sẵn sàng để kiểm tra. RQ3 sẽ kiểm tra được nếu việc sửa tiêu đề tạo ra các nhóm $\ge 5$ tin — và bảng phân nhóm ở mục 4 cho thấy chắc chắn sẽ đạt được.
