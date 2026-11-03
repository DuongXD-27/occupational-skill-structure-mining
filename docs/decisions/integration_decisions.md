# Quyết định chung về phạm vi và tích hợp

Ngày chốt: 2026-10-03. Người chịu trách nhiệm: Dương.
Áp dụng cho crawler, cleaner, skill extractor và analysis; schema hiện tại gồm 22 trường.

## A. Phân công câu hỏi nghiên cứu

| Công việc | Người phụ trách | Đầu vào |
|---|---|---|
| Thu thập dữ liệu | Đạt | Nguồn được phê duyệt |
| Cleaner, chuẩn hóa chức danh và RQ1 | Đức | Dữ liệu crawler |
| Trích xuất kỹ năng, danh sách kỹ năng và ma trận job–skill | Cường (từ 2026-11-03: duyệt gold, alias, số liệu P/R/F1; xem mục F) | Dữ liệu sạch, taxonomy |
| RQ2–RQ4 | Triều | Dữ liệu sạch, đặc trưng kỹ năng |
| Phạm vi, schema, điều phối và nghiệm thu tích hợp | Dương | Các module bàn giao |

Đức phụ trách RQ1: số tin hợp lệ, số chức danh gốc/sau chuẩn hóa, tỷ lệ nén,
entropy, tỷ lệ chức danh hiếm và các đầu ra trong [đặc tả phân tích](../analysis/analysis_spec.md).
Tỷ lệ nén giữ định nghĩa hiện có: số chức danh chuẩn hóa / số chức danh thô.
Triều phụ trách RQ2–RQ4. RQ1 có thể chạy ngay sau cleaner, độc lập với parser.
Các giới hạn mẫu nhỏ trong đặc tả phân tích vẫn áp dụng; không công bố chỉ số chưa đủ dữ liệu.

## B. Lương và học vấn

Quyết định hiện hành ngày 2026-10-04: bỏ `salary_raw` và `education`, giảm schema
từ 24 xuống 22 trường. Hai trường không phục vụ RQ1–RQ4. Crawler không trích xuất
lương hoặc học vấn riêng; cleaner không tạo/xuất các cột đó. Nội dung lương/học
vấn vốn có trong mô tả hoặc yêu cầu vẫn được bảo toàn cùng văn bản nguồn.

Mẫu 45 tin được chuyển đổi bằng cách bỏ hai cột đang toàn `null`; các giá trị còn
lại được giữ nguyên. Khi chuyển đổi dữ liệu cũ có giá trị ở các cột bị bỏ, giữ bản
lưu trữ rồi tạo bảng schema mới. Chỉ bổ sung lại trường riêng nếu phạm vi nghiên
cứu sau này cần đến chúng.

### Lịch sử rút gọn schema

Thay đổi schema được Dương chốt ngày 2026-10-03: bỏ `salary_min`, `salary_max`,
`salary_currency`, giảm từ 29 xuống 26 trường ở bước này. Mẫu 45 tin được chuyển đổi bằng cách bỏ
ba cột phái sinh đang toàn `null`, giữ nguyên tất cả giá trị còn lại, gồm `salary_raw`.
Dữ liệu cũ có lương phái sinh khác `null` phải được lưu lại ở bản lưu trữ trước
khi tạo bản theo schema mới; không đưa ba cột cũ vào bảng chính của pipeline.

Ngày 2026-10-04, Dương chốt tiếp việc bỏ `experience_min_years` và
`experience_max_years`, giảm schema từ 26 xuống 24 trường. Chỉ giữ
`raw_experience: string/null`: có dữ liệu nguồn thì lưu nguyên văn, không có thì
`null`. Không parse số năm, suy diễn từ cấp bậc hoặc bóc tách bổ sung từ mô tả.
Hai trường phái sinh không phục vụ RQ1–RQ4 hiện tại; chỉ xem xét bổ sung khi
phạm vi nghiên cứu cần phân tích kinh nghiệm.

Ở bước tiếp theo, schema còn 24 trường. Mẫu 45 tin được chuyển đổi
bằng cách bỏ hai cột kinh nghiệm phái sinh toàn `null`, giữ nguyên mọi giá trị còn
lại. Với dữ liệu cũ có số năm đã parse, lưu bản cũ trước khi tạo bảng schema mới.

## C. Chức danh thô và chuẩn hóa

`raw_job_title` lưu trung thành với nội dung chức danh tại nguồn. Crawler không
ghép thêm skill tags, tech stack hoặc metadata từ thành phần khác vào chức danh,
và không xóa phần công nghệ vốn có trong chính chức danh nguồn.

Ví dụ nguồn ghi `Data Analyst (Azure, SQL, NoSQL, Power BI)` thì `raw_job_title`
phải lưu đúng nội dung này. Đức quyết định xử lý hậu tố công nghệ rõ ràng ở
`normalized_job_title`, đồng thời tài liệu hóa quy tắc và giữ nguyên trường thô.
Không xóa mọi phần trong ngoặc một cách máy móc: phần đó có thể mô tả chuyên môn hoặc vai trò.

Quy ước cho ví dụ đã chốt:

| `raw_job_title` | `normalized_job_title` |
|---|---|
| `Senior Data Analyst` | `Data Analyst` |
| `Data Analyst` | `Data Analyst` |
| `DATA ANALYST` | `Data Analyst` |

Chuẩn hóa cấp bậc như `Senior` trong ví dụ trên phục vụ so sánh chức danh cơ sở,
không có nghĩa chuyển cấp bậc thành số năm kinh nghiệm. Vai trò quản lý/lead,
chuyên môn và chức danh ghép phải được Đức xử lý có quy tắc cụ thể; không mặc định
gộp `AI Engineer`, `Machine Learning Engineer` và `Data Scientist`.

Thông tin audit 19/45 bản ghi có vấn đề title là đầu vào do Dương cung cấp cho
quyết định này, chưa phải kết quả kiểm chứng lại với trang nguồn trong đợt tích hợp.
Cần phân biệt phần công nghệ vốn có tại nguồn với phần bị crawler ghép thêm trước khi sửa crawler.

## D. Hợp đồng bàn giao

Cleaner giữ các bản ghi trong bảng sạch để kiểm toán, gán `relevance_flag`,
`duplicate_flag` và lý do loại trừ. Tập dùng cho RQ và trích xuất kỹ năng là
`relevance_flag=true AND duplicate_flag=false`. Trường hợp bị loại bởi cả hai cờ
được báo cáo riêng, tránh cộng hai lần số tin bị loại.

Cleaner tạo `normalized_job_title` và `job_text`, không ghi đè dữ liệu gốc.
Skill extractor xuất danh sách kỹ năng và ma trận đúng tập `job_id` hợp lệ.
Danh sách dùng `canonical_name`; cột ma trận dùng `skill_id` và được kiểm tra
qua taxonomy. Chi tiết API ở [hướng dẫn pipeline](../pipeline/README.md).

`quality_flags` hiện chưa thuộc schema 22 trường. Ghi vào log riêng theo phương án
dự phòng trong quy tắc chất lượng; không tự thêm vào bảng chính. Khung tích hợp
báo lỗi nếu gặp trường ngoài schema, thay vì tự xóa dữ liệu của thành viên.

## E. Phụ thuộc và nghiệm thu

Đạt và Đức dùng quyết định C trước khi xuất bản dữ liệu cuối. Dương chốt mọi thay
đổi về phạm vi, schema và tiêu chuẩn giữ/loại tin; thành viên không thay đổi các
quy ước này để phù hợp với code riêng.

Dương triển khai khung tích hợp từ bây giờ. Nghiệm thu nghiên cứu cuối chỉ thực hiện
sau khi Đạt, Đức, Cường và Triều bàn giao module, kiểm thử với module thật và đáp ứng
các yêu cầu đánh giá nghiên cứu. Module giả lập chỉ dùng kiểm thử ranh giới bàn giao.

Nguồn chính tiếp tục là ITviec; TopCV là dự phòng. Xem [so sánh nguồn](../data_collection/source_comparison.md).

## F. Quyết định ngày 2026-11-03

Dương chốt các điểm dưới đây. Mốc chính: **chốt dữ liệu 2026-11-23**, báo cáo
kết quả giữa tháng 12/2026.

1. **Bật TopCV làm nguồn thứ hai.** Điều kiện kích hoạt ở phạm vi §7 đã xảy ra:
   đợt thu ITviec 30/09 quét hết các danh mục hạt giống và chỉ được 252 tin
   (211 tin hợp lệ sau làm sạch), không đủ 300 tin cho RQ4. Kết quả khảo sát nguồn ở
   [source_inspection.md](../data_collection/source_inspection.md#topcv). Bản ghi
   TopCV dùng cùng schema 22 trường, cùng tiêu chí giữ/loại, giữ `source=TopCV`
   và `source_url`. Vẫn tối đa hai nguồn.
2. **Bản sửa sau review được đẩy thẳng vào nhánh của thành viên** (PR #12–#16);
   người phụ trách duyệt lại trong 2 ngày. Thứ tự merge: #15 → #12 → #13 → #14 → #16.
3. **Gold kỹ năng.** Cường và Dương duyệt. Mỗi người gán độc lập cùng 15–20 tin
   trước để đo độ đồng thuận (Cohen's kappa), sau đó mới duyệt phần còn lại từ bản
   nháp Codex. Mở rộng lên 100 tin nếu kịp tiến độ.
4. **Phân công lại.** Cường chịu trách nhiệm duyệt gold, bổ sung alias và số liệu
   P/R/F1; Dương giữ phần điều phối, schema và nghiệm thu.
5. **Chuẩn hóa chức danh** theo quy tắc đã cài trong cleaner: chỉ bỏ cấp bậc thuần túy
   (Senior/Junior/Middle/Fresher); giữ Lead, Intern, Head; chỉ bỏ ngoặc/hậu tố khi
   mọi mục là công cụ trong taxonomy; giữ phần chuyên môn như `- Computer Vision`,
   `(LLM/RAG)`.
6. **Luồng trùng gần chỉ dựa trên mô tả (cosine ≥ 0,95) giữ tắt.** QR-05 giữ đủ bốn
   điều kiện AND. Cặp MB Bank #36/#40 được ghi vào phần hạn chế.
7. **Khung thời gian quan sát:** tin thu được từ 2026-09-30 đến 2026-11-23. Cùng
   `source_url` thu nhiều lần thì giữ bản thu sớm nhất.
8. **Pilot thu bằng parser v0.2:** thu lại bằng v0.3 các tin còn đang đăng. Tin đã gỡ
   giữ bản v0.2 (phân biệt bằng `parser_version`) và ghi vào phần hạn chế.
9. **Khóa taxonomy và parser ngày 2026-11-23.** Gold được chia cố định thành hai
   nửa theo `job_id`: nửa `tune` dùng để chỉnh alias, nửa `holdout` dùng để báo cáo
   P/R/F1 chính thức (`python -m src.parser evaluate --subset holdout`).
10. **Ngưỡng phân tích giữ nguyên** (mục 7 đặc tả). Thêm điều kiện: RQ3 chỉ báo cáo khi
    có ít nhất 3 chức danh đạt 5 tin.
11. **Quy tắc chọn k:** độ ổn định cao nhất (trong biên 0,02) → silhouette cao nhất
    (trong biên 0,02) → k nhỏ hơn. Đặc tả đã sửa câu chữ cho khớp; chốt trước khi chạy.
12. **Không làm mô hình dự đoán chức danh** cho RQ3.
13. **Nếu đến 2026-11-23 vẫn dưới 300 tin hợp lệ:** không hạ ngưỡng. RQ4 được trình bày
    như phương pháp đã kiểm chứng trên dữ liệu giả lập; RQ1–RQ3 báo cáo đầy đủ.
