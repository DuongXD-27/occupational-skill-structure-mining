# So sánh nguồn phục vụ quyết định thu thập

Rà soát tài liệu trong repo ngày 2026-10-03. Đây là tổng hợp bằng chứng đã có,
không phải khảo sát trực tuyến mới hoặc xác nhận điều kiện truy cập hiện tại.

| Tiêu chí | ITviec | TopCV |
|---|---|---|
| Vai trò được chốt | Nguồn chính | **Nguồn thứ hai, đã kích hoạt 2026-11-03** |
| Bằng chứng trong repo hiện tại | Crawler, pilot 252 tin (toàn bộ danh mục hạt giống 30/09) | Khảo sát robots.txt và điều khoản ([source_inspection](source_inspection.md#topcv)); crawler đang viết |
| Văn bản phục vụ trích xuất | Báo cáo mẫu ghi nhận mô tả và yêu cầu ở 45 tin | Chưa kiểm chứng |
| Lương và học vấn trong pipeline | Ngoài phạm vi; không thu thập riêng hoặc xuất cột | Áp dụng cùng chính sách nếu kích hoạt |
| Schema | Tuân thủ 22 trường; cần rà soát độ trung thành của title | Bắt buộc tuân thủ cùng schema nếu kích hoạt |
| Điều kiện kích hoạt | Thu thập thông thường | Khi ITviec không truy cập được, không khả thi hoặc không cung cấp đủ tin hợp lệ |
| Việc còn phải làm trước crawl lớn | Kiểm tra điều khoản, robots, giới hạn truy cập và selector hiện tại | Khảo sát tương tự, chạy pilot và ghi nhận bằng chứng trước khi sử dụng |

Bằng chứng: [khảo sát ITviec](source_inspection.md),
[kiểm tra dữ liệu mẫu](../../reports/analysis/sample_analysis_check.md),
[phạm vi nguồn](../project_scope.md#8-phạm-vi-nguồn-dữ-liệu).

Ngày 2026-11-03 Dương kích hoạt TopCV vì ITviec không cung cấp đủ tin hợp lệ
(252 tin là toàn bộ tin Data/AI trên các danh mục hạt giống; cần ≥ 300 tin hợp lệ cho
RQ4). Không bổ sung nguồn thứ ba. Bản ghi TopCV bảo toàn `source`, `source_url`,
áp dụng cùng tiêu chí Data/AI; xem [quyết định F.1](../decisions/integration_decisions.md#f-quyết-định-ngày-2026-11-03).

Tài liệu này phù hợp với phạm vi nguồn đã chốt và có thể đưa vào `main` cùng khung
tích hợp. Các nhận xét trong báo cáo ITviec là quan sát của đợt khảo sát cũ.
Không dùng chúng để suy ra TopCV đã được kiểm chứng hoặc để vượt CAPTCHA/xác thực.
