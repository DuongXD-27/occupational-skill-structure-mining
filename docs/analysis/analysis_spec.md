# ĐẶC TẢ PHÂN TÍCH (ANALYSIS SPECIFICATION)

**Người phụ trách:** Hồ Nhật Triều (20236003) · **Chỉnh lý:** 2026-09-24 (chỉ điều chỉnh cách diễn đạt — phương pháp giữ nguyên)

**Mục đích tài liệu:** Kế hoạch chi tiết cho giai đoạn phân tích — chúng ta tính toán những gì, đầu ra gồm những bảng/biểu đồ nào, và khi nào thì một kết quả đủ độ tin cậy an toàn để công bố.

Tài liệu được soạn thảo trước khi có dữ liệu đầy đủ một cách có chủ đích, nhằm đảm bảo các ngưỡng định lượng được thiết lập dựa trên lập luận khoa học chứ không phải chọn lựa sau đó để làm đẹp số liệu.

---
---

# 1. BỐN CÂU HỎI NGHIÊN CỨU

| | Câu hỏi | Chúng ta thực hiện những gì |
|---|---|---|
| **RQ1** | Những chức danh công việc nào tồn tại, và mỗi chức danh phổ biến ra sao? | Đếm số lượng, đo lường mức độ phân mảnh trong cách đặt tên của thị trường |
| **RQ2** | Những kỹ năng nào được yêu cầu nhiều nhất, và những kỹ năng nào đi liền với nhau? | Thống kê tần suất kỹ năng, đếm các cặp kỹ năng cùng xuất hiện trong một tin tuyển dụng |
| **RQ3** | Chức danh công việc có khớp với kỹ năng được yêu cầu hay không? | Cùng chức danh → kỹ năng khác nhau? Khác chức danh → kỹ năng giống nhau? |
| **RQ4** | Ẩn chức danh đi — dữ liệu tự hình thành nên những nhóm việc làm nào? | Phân cụm thuần túy trên không gian kỹ năng, sau đó đối chiếu lại với chức danh thực tế |

RQ4 là câu hỏi trọng tâm nhất. RQ1–RQ3 đóng vai trò xây dựng nền tảng dẫn dắt tới RQ4.

---
---

# 2. DỮ LIỆU ĐẦU VÀO PHẢI NHƯ THẾ NÀO

Tên các trường dữ liệu tuân thủ nghiêm ngặt [docs/data_schema.md](docs/data_schema.md) các mục 5, 8 và 13. Bản đặc tả này sử dụng chính xác các tên trường đó — không sử dụng tên alias.

Danh sách trường: `job_id` · `raw_job_title` · `normalized_job_title` · `company` · `raw_location` · `normalized_location` · `job_description` · `job_requirements` · `extracted_skills` · `skill_count` · `relevance_flag` · `source` · `source_url` · `crawl_timestamp`

Không phải câu hỏi nào cũng dùng tất cả các trường — ví dụ RQ2 chỉ cần `job_id` và `extracted_skills`.

## Bốn quy tắc đối với `extracted_skills` và `raw_job_title`

| Quy tắc | Lý do |
|---|---|
| `extracted_skills` phải là một danh sách (list), không phải một chuỗi đơn | Chuỗi đơn sẽ phải tách sau này, và tên kỹ năng chứa dấu phẩy sẽ làm hỏng thao tác split |
| Trường này chứa mã taxonomy, không chứa từ ngữ thô | `sklearn` và `scikit-learn` nếu đến riêng lẻ sẽ bị chia thành 2 kỹ năng và làm ẩn đi nhu cầu thực tế |
| Không tìm thấy kỹ năng → danh sách rỗng `[]`, tuyệt đối không để `null` | Danh sách rỗng = tin tuyển dụng viết kém. Null = bộ trích xuất chưa từng chạy. Hai lỗi khác nhau cần cách xử lý khác nhau |
| `raw_job_title` không bao giờ bị ghi đè | RQ1 đếm số chức danh thô khác biệt; ghi đè sẽ phá hủy phép đo này (cũng theo Scope §10) |

---
---

# 3. RQ1 — NHỮNG CHỨC DANH CÔNG VIỆC NÀO TỒN TẠI

| Chỉ số (Metric) | Lý do |
|---|---|
| Số tin tuyển dụng giữ lại sau làm sạch | Mọi tỷ lệ phần trăm sau này đều chia cho mẫu số này |
| Số chức danh thô khác biệt / số chức danh chuẩn hóa khác biệt | Có bao nhiêu tên gọi trước và sau khi dọn dẹp bề mặt (thô = chỉ trim + lowercase) |
| Tỷ lệ nén (Compression ratio = normalized ÷ raw) | Thấp → sự đa dạng chỉ là do định dạng bề mặt. Gần 1 → nhà tuyển dụng thực sự dùng rất nhiều tên khác nhau |
| Độ tập trung (Concentration) | Một vài chức danh có chiếm phần lớn số lượng tin tuyển dụng không? |
| Độ hỗn loạn (Entropy) | Đo lường cùng một bản chất từ góc nhìn khác — entropy cao nghĩa là nhu cầu phân bổ đều. Cả hai chỉ số được báo cáo để kiểm tra chéo |
| Tỷ lệ chức danh hiếm ($\le 2$ tin) | Các chức danh hiếm thường là do một nhà tuyển dụng tự sáng chế ra |
| Các công ty đứng sau những chức danh hiếm đó | 50 chức danh kỳ lạ đến từ 3 công ty nghĩa là *"một vài công ty tự nghĩ ra tên"*, chứ không phải *"thị trường bị phân mảnh"*. Không có chỉ số này sẽ dẫn tới kết luận sai |

Đầu ra — 3 bảng: Bảng tổng hợp · Top 20 chức danh phổ biến · Danh sách chức danh hiếm kèm tên công ty và URL.  
2 biểu đồ: Biểu đồ cột cho Top 20 · Biểu đồ hạng - tần suất (rank-frequency) trên thang log-log.

---
---

# 4. RQ2 — NHỮNG KỸ NĂNG NÀO ĐƯỢC YÊU CẦU NHIỀU NHẤT

| Chỉ số (Metric) | Lý do |
|---|---|
| Tần suất kỹ năng (Skill frequency) | Câu hỏi thực tế nhất của dự án — một người thực sự nên học những kỹ năng gì? |
| Số kỹ năng trên mỗi tin (trung bình, trung vị, p10, p90) | Kiểm tra sức khỏe của bộ trích xuất. Trung bình bằng 2 nghĩa là việc trích xuất bị hỏng và mọi thứ ở hạ nguồn sẽ sai lệch |
| Số lần đồng xuất hiện (Co-occurrence count) | Các kỹ năng thường đi cùng nhau — một tin tuyển dụng cần PyTorch thường cũng cần CUDA |

Sau đó áp dụng ba thước đo để đánh giá xem một cặp kỹ năng thực sự liên kết với nhau hay chỉ đơn giản là cả hai đều phổ biến:

| Thước đo | Bản chất đo lường | Điểm yếu |
|---|---|---|
| **Lift** | Tần suất cặp kỹ năng xuất hiện cùng nhau cao hơn bao nhiêu lần so với trường hợp ngẫu nhiên | Bị phóng đại đối với các cặp kỹ năng hiếm |
| **Normalized PMI** | Cùng ý tưởng với Lift, nhưng được co giãn về đoạn $[-1, 1]$ | — |
| **Jaccard** | Số tin có cả 2 kỹ năng ÷ số tin có ít nhất 1 kỹ năng | Bị thiên lệch ưu tiên các cặp kỹ năng phổ biến |

Sử dụng cả ba thước đo, bởi vì mỗi thước đo có một điểm yếu khác nhau. Một cặp kỹ năng thể hiện mạnh dưới cả ba thước đo chắc chắn là một liên kết thực sự.

Cộng đồng kỹ năng: xây dựng đồ thị mạng lưới từ các cặp kỹ năng và để thuật toán tự chia thành các phân vùng chuyên môn, thay vì gom nhóm kỹ năng thủ công bằng tay.

Đầu ra — 4 bảng: Tần suất kỹ năng · Top 30 cặp kỹ năng theo từng thước đo · Các cộng đồng kỹ năng phát hiện được · Các cặp kỹ năng liên kết âm (ít đi cùng nhau).  
3 biểu đồ: Biểu đồ Top 30 kỹ năng · Heatmap liên kết · Đồ thị mạng lưới đồng xuất hiện kỹ năng.

---
---

# 5. RQ3 — CHỨC DANH CÓ KHỚP VỚI KỸ NĂNG YÊU CẦU KHÔNG

## Kiểm tra 1 — cùng chức danh, kỹ năng có khác nhau không?

So sánh từng cặp tin tuyển dụng có chung chức danh, đo lường mức độ khác biệt của chúng. Độ khác biệt cao → tên chức danh mang rất ít thông tin thực chất.

Một con số thô ở đây không mang nhiều ý nghĩa. Điểm số 0.62 tự nó không nói lên điều gì. Do đó, đối với mỗi chức danh, chúng ta rút ngẫu nhiên một nhóm tin có cùng kích thước từ toàn bộ tập dữ liệu, đo độ phân tán của nó, và lặp lại 1.000 lần (bootstrap baseline). Nếu chức danh thật rơi vào khoảng ngẫu nhiên đó, chức danh đó không đem lại thông tin tốt hơn một nhãn dán ngẫu nhiên. Cùng kích thước là yếu tố cốt tử — các nhóm nhỏ luôn có độ nhiễu cao hơn.

## Kiểm tra 2 — khác chức danh, kỹ năng có giống nhau không?

Xây dựng một hồ sơ (profile) cho mỗi chức danh (vector kỹ năng trung bình của các tin thuộc chức danh đó), so sánh các profile với nhau. Độ tương đồng cao → hai tên gọi khác nhau đang mô tả cùng một công việc.

Đầu ra — 4 bảng: Độ phân tán nội bộ từng chức danh kèm baseline đối chứng · Các cặp chức danh tương đồng kèm kỹ năng chung và kỹ năng phân hóa · Các cặp bị cảnh báo tại 3 ngưỡng · Hồ sơ kỹ năng của từng chức danh.  
3 biểu đồ: Biểu đồ độ phân tán so với baseline · Biểu đồ phân cấp Dendrogram của chức danh · Heatmap tương đồng chức danh - chức danh.

---
---

# 6. RQ4 — ĐỂ THUẬT TOÁN TỰ GOM NHÓM VIỆC LÀM

Phân cụm hoàn toàn trên không gian kỹ năng, chức danh được giấu kín. Sau khi phân cụm xong, ghép chức danh trở lại và chấm điểm mức độ đồng thuận (agreement score).

Điểm gần 1 → dữ liệu tự tái lập lại chính xác các chức danh mà nhà tuyển dụng đang sử dụng.  
Điểm gần 0 → chức danh và công việc thực tế đã tách rời nhau.

Bất kỳ kết quả nào cũng đều là một phát hiện khoa học. Đây chính là con số trọng tâm của toàn bộ báo cáo nghiên cứu.

## Lựa chọn số lượng cụm (k)

Quét $k$ từ 2 đến 15, đánh giá mỗi giá trị theo ba tiêu chí:

- **Silhouette** — mức độ phân tách rõ ràng giữa các cụm. Càng cao càng tốt.
- **Davies-Bouldin** — độ phân tán bên trong cụm so với khoảng cách giữa các cụm. Càng thấp càng tốt.
- **Độ ổn định (Stability)** — phân cụm lại trên 80% mẫu ngẫu nhiên, lặp lại 100 lần, kiểm tra xem các tin có tiếp tục ở cùng nhau không.

Quy tắc chọn $k$: ưu tiên độ ổn định cao nhất → nếu hòa nhau thì chọn Silhouette cao hơn → nếu chênh lệch độ ổn định trong khoảng 0.02, chọn giá trị $k$ nhỏ hơn.

Độ ổn định được xếp hạng cao hơn có chủ đích. Một cụm có thể trông rất tách biệt nhưng lại biến mất khi lấy mẫu lại — và nếu nó biến mất, nó chỉ là đặc thù ngẫu nhiên của mẫu dữ liệu này, không phải của thị trường.

Công bố toàn bộ kết quả quét, không chỉ mỗi giá trị chiến thắng, để người đọc có thể tự kiểm chứng quyết định thay vì phải tin tưởng một cách mù quáng.

## Hai quy tắc đảm bảo tính khách quan trung thực

**Phương pháp thử mù (Blinding):** Nhãn cụm phải được ghi ra file và commit vào Git *trước khi* ghép nối chức danh trở lại. Một khi đã nhìn thấy chức danh, người nghiên cứu không thể chọn $k$ một cách khách quan nữa.

`skill_group` không phải là đầu vào của thuật toán. Cột nhóm kỹ năng do con người gán chỉ dùng để đối chiếu so sánh sau đó. Đưa nó vào làm đặc trưng phân cụm sẽ bị lỗi logic vòng tròn (circular reasoning) — tự tay nhóm trước rồi "tái khám phá" lại chính các nhóm đó.

Đầu ra — 5 bảng: Kết quả quét qua các giá trị $k$ · Hồ sơ đặc trưng từng cụm · Bảng chéo Cụm $\times$ Chức danh · Điểm số đồng thuận · Các tin tuyển dụng ví dụ đại diện cho mỗi cụm.  
4 biểu đồ: Biểu đồ quét chọn $k$ · Biểu đồ PCA tô màu theo Cụm · Biểu đồ PCA tô màu theo Chức danh · Heatmap Cụm $\times$ Chức danh.

Hai biểu đồ PCA được đặt cạnh nhau. Điểm số đồng thuận trừu tượng rất khó hình dung; hai bức tranh không khớp nhau sẽ được thấu hiểu ngay lập tức — và sự khác biệt giữa chúng *chính là* câu trả lời cho RQ4.

---
---

# 7. CÁC NGƯỠNG ĐỊNH LƯỢNG

| Ngưỡng | Giá trị | Cơ sở lý luận |
|---|---|---|
| Số tin trên mỗi chức danh (RQ3) | $\ge 5$ | 5 tin tạo ra 10 cặp so sánh. Dưới ngưỡng đó, giá trị trung bình không thể phân biệt được với sự ngẫu nhiên |
| Số tin trên mỗi kỹ năng | $\ge 3$ | Dưới 3 tin, kỹ năng chỉ là nhiễu |
| Số lần đồng xuất hiện của mỗi cặp | $\ge 5$ | Lift biến động rất mạnh dưới ngưỡng này — chỉ cần một lần tình cờ đi cùng nhau sẽ tạo ra giá trị cực đoan |
| Số kỹ năng trên mỗi tin (đo tương đồng) | $\ge 2$ | 1 kỹ năng thì không có gì để so sánh. Vẫn được tính trong tần suất kỹ năng, chỉ loại khỏi phép đo tương đồng và phân cụm |
| Số tin tối thiểu để phân cụm | $\ge 300$ | Bất kỳ cụm nào tìm thấy dưới quy mô này đều chỉ là ngẫu nhiên |

Tất cả năm ngưỡng này là đề xuất phương pháp luận và cần được xem xét lại khi quy mô tập dữ liệu thực tế được xác lập. Mọi thay đổi sau này phải được ghi nhận kèm lý do rõ ràng.

---
---

# 8. NHỮNG PHÉP PHÂN TÍCH KHÔNG THỂ CHẠY TRÊN MẪU NHỎ

Áp dụng cho tập mẫu 30–50 tin tuyển dụng.

Có thể chạy thử như một bài kiểm thử pipeline — tuyệt đối không coi là phát hiện nghiên cứu: đếm số tin, đếm chức danh, tần suất kỹ năng, số kỹ năng/tin, các bước kiểm tra chất lượng.

| Phân tích bắt buộc phải bỏ | Lý do |
|---|---|
| Độ tập trung, entropy, chức danh hiếm | Cần một phân phối thực tế. Ở quy mô 40 tin, hầu như mỗi chức danh chỉ xuất hiện một lần |
| Phân tích cặp kỹ năng | Hầu như không có cặp kỹ năng nào đạt ngưỡng 5 lần đồng xuất hiện |
| Cả 2 phép kiểm tra của RQ3 | Hầu như không có chức danh nào đạt 5 tin; một profile từ 1–2 tin chỉ phản ánh chính những tin đó |
| Toàn bộ RQ4 | 40 tin so với ngưỡng tối thiểu bắt buộc là 300 tin |

Các phân tích này phải được loại bỏ hoàn toàn, không công bố kèm cảnh báo. Một con số được công bố kèm lời cảnh báo vẫn sẽ bị người khác trích dẫn như một con số thực tế.

---
---

# 9. KIỂM SOÁT CHẤT LƯỢNG VÀ TÍNH TÁI LẬP

Tám kiểm tra chất lượng phải chạy trước bất kỳ phân tích nào. Một kiểm tra thất bại sẽ chuyển trả công việc về khâu thu thập hoặc làm sạch, không được phép đưa vào biểu đồ báo cáo.

Tầm quan trọng: một bộ trích xuất yếu tạo ra danh sách kỹ năng ngắn → danh sách ngắn làm cho mọi tin trông đều khác biệt → điều đó làm thổi phồng độ phân tán và làm suy yếu mọi mối liên kết. Lỗi kỹ thuật sẽ tạo ra chính xác kết luận mà chúng ta kỳ vọng một cách giả tạo, thay vì kiểm chứng nó một cách khách quan.

Tính tái lập: cố định một giá trị seed ngẫu nhiên, toàn bộ ngưỡng nằm trong một file cấu hình, mọi bảng kết quả đều có tiêu đề ghi rõ quy mô dữ liệu và đặc tả được sử dụng — để mỗi con số đều minh bạch về nguồn gốc dữ liệu mà nó đứng trên.

---
---

# 10. CÁC CÂU HỎI THẢO LUẬN CHO NHÓM

1. **Trưởng nhóm (Leader):** Câu hỏi quan trọng nhất. Vị trí `Senior Data Analyst` có được tính là `Data Analyst` không? Nếu giữ tách biệt, rất nhiều chức danh sẽ rơi xuống dưới ngưỡng 5 tin và RQ3 sẽ mất phần lớn mẫu nghiên cứu.
2. **Người phụ trách Taxonomy:** Có bao nhiêu kỹ năng trong taxonomy? Điều này quyết định ngưỡng lọc kỹ năng và quy mô tối thiểu 300 tin.
3. **Người phụ trách Taxonomy:** Có cột `skill_group` không? Mục 6 chỉ sử dụng cột này để đối chiếu so sánh sau cùng.
4. **Người phụ trách Thu thập:** Dữ liệu mẫu đã trả lời: `job_description` và `job_requirements` tách biệt và đầy đủ trên cả 45 tin. Câu hỏi còn lại: `relevance_flag` và `exclusion_reason` đang null trên cả 45 tin — khâu thu thập sẽ gán hay khâu làm sạch gán?
5. **Trưởng nhóm (Leader):** Có nên bổ sung một mô hình dự đoán chức danh như một thước đo phụ cho RQ3 không? Nó sẽ cô đọng RQ3 thành một con số nổi bật duy nhất. Hiện không nằm trong phạm vi bắt buộc của đề tài — đưa ra để xin ý kiến thảo luận, không tự ý mặc định.
