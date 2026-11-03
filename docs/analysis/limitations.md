# HẠN CHẾ CỦA NGHIÊN CỨU (bản nháp, 2026-11-03)

Bản nháp để đưa vào chương "Hạn chế" của báo cáo. Những chỗ ghi `[điền sau 23/11]` sẽ có số liệu sau khi chốt dữ liệu ngày 23/11 (integration_decisions F.7, F.9).

## 1. Dữ liệu

| Hạn chế | Ảnh hưởng | Cách nhóm xử lý / cách đọc kết quả |
|---|---|---|
| Chỉ hai nguồn (ITviec, TopCV), một quốc gia, cửa sổ quan sát 2026-09-30 → 2026-11-23 | Không đại diện cho toàn bộ thị trường hay xu hướng theo thời gian; tuyển dụng có tính mùa vụ | Mọi kết luận đều ghi rõ là "tin đăng trên hai nguồn trong cửa sổ này". Không có phân tích xu hướng |
| Cỡ mẫu nhỏ: khoảng [điền sau 23/11] tin hợp lệ | Nhiều chức danh dưới 5 tin, nhiều cặp kỹ năng dưới 5 lần đồng xuất hiện | Các ngưỡng ở analysis_spec §7 loại bỏ những phép đo không đủ dữ liệu, và phần bị loại được liệt kê thay vì lặng lẽ biến mất (`rq3_skipped_titles.csv`). Nếu dưới 300 tin, RQ4 chỉ là phần trình diễn phương pháp trên dữ liệu giả (F.13) |
| Tin tuyển dụng ≠ công việc thực tế | Tin đăng thường liệt kê kỹ năng "mong muốn" quá rộng, sao chép mẫu tin cũ | RQ2–RQ4 trả lời câu hỏi "nhà tuyển dụng *viết* gì", không phải "người làm nghề *làm* gì" |
| Trùng lặp giữa hai nguồn và giữa các lần đăng lại | Một vị trí bị đếm nhiều lần, làm phồng tần suất | Khử trùng chính xác và gần đúng (cùng công ty + title + mô tả); chế độ chỉ dựa vào mô tả bị tắt (F.6), nên cặp đăng lại khác tiêu đề như MB Bank #36/#40 vẫn còn; QC6 kiểm tra phần còn sót |
| Một phần pilot ITviec thu bằng parser v0.2; tin đã gỡ không thu lại được bằng v0.3 (F.8) | Hai phiên bản parser có thể tách văn bản hơi khác nhau | Phân biệt bằng `parser_version`; báo cáo số tin mỗi phiên bản |
| Điều khoản sử dụng của TopCV (§6.2) hạn chế sao chép và tạo sản phẩm phái sinh | Không thể công bố dữ liệu thô | Chỉ công bố số liệu tổng hợp; dữ liệu thô không đưa lên kho mã công khai. Cần xác nhận với giảng viên hướng dẫn |

## 2. Trích xuất kỹ năng

| Hạn chế | Ảnh hưởng | Cách xử lý |
|---|---|---|
| Bộ trích xuất dựa trên từ điển (taxonomy + alias), không hiểu ngữ cảnh | Bỏ sót kỹ năng diễn đạt gián tiếp; bắt nhầm khi một từ có nhiều nghĩa | Đánh giá trên tập gold 50 tin, chia tune/holdout (F.9): P/R/F1 trên holdout = [điền sau khi duyệt gold]. Bản nháp do Codex gán trên toàn bộ 50 tin: P 96,3% · R 85,3% · F1 90,5% |
| Tập gold được mô hình gán nháp rồi người duyệt; chỉ 15–20 tin được hai người gán độc lập | Độ đồng thuận chỉ đo trên một phần nhỏ; phần còn lại có thể nghiêng theo bản nháp | Đo Cohen's kappa trên phần gán độc lập (F.3) = [điền sau]; báo cáo số nhãn nháp bị người duyệt sửa |
| Thiếu recall (khoảng 15%) làm danh sách kỹ năng ngắn hơn thực tế | Làm phồng độ phân tán RQ3 và làm yếu các liên kết RQ2 (analysis_spec §9) | Các kiểm tra QC3–QC4; baseline ngẫu nhiên cùng cỡ ở RQ3 chịu cùng mức thiếu recall nên phép so sánh vẫn công bằng |
| Taxonomy và parser bị khoá ngày 23/11 (F.9) | Kỹ năng mới xuất hiện sau đó không được bắt | Ghi phiên bản taxonomy trong manifest của mỗi lần chạy |

## 3. Chuẩn hoá chức danh

Chuẩn hoá chức danh dựa trên luật (bỏ cấp bậc, bỏ hậu tố công nghệ, bỏ cụm từ quảng cáo tuyển dụng). Hai title thực chất giống nhau vẫn có thể còn tách riêng, và ngược lại. RQ3 và RQ4 đo đúng độ lệch này nên kết quả nhạy với luật chuẩn hoá: báo cáo cần nêu số title thô và số title sau chuẩn hoá (RQ1).

## 4. Phương pháp phân tích

| Hạn chế | Cách đọc kết quả |
|---|---|
| Các ngưỡng (≥5 tin/title, ≥5 lần đồng xuất hiện, ≥300 tin để phân cụm, 3 ngưỡng cosine) là lựa chọn phương pháp luận, không phải giá trị chuẩn | Đã chốt trước khi xem dữ liệu thật (F.10–F.11); không đổi sau khi xem kết quả |
| K-Means giả định cụm dạng cầu; vector kỹ năng nhị phân và thưa | Có phân cụm phân cấp (Jaccard, average) làm đối chứng. Kết luận chỉ mạnh khi hai phương pháp đồng thuận (`rq4_method_agreement.csv`) |
| ARI/NMI so với chức danh phụ thuộc chất lượng chuẩn hoá chức danh | Đọc cùng heatmap cụm × chức danh, không chỉ một con số |
| Không có mô hình dự đoán chức danh (F.12) | Nghiên cứu mang tính mô tả và khám phá, không đưa ra khẳng định nhân quả |
