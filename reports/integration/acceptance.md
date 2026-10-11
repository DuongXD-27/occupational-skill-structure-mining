# Báo cáo bàn giao khung tích hợp

Ngày đánh giá: 2026-10-04. Trạng thái: **đạt kiểm thử khung tích hợp; chờ nghiệm thu module thật**.

## 1. Phần đã bàn giao

| Kết quả | Bằng chứng |
|---|---|
| Quyết định RQ1, lương/học vấn, title và phụ thuộc | [Quyết định chung](../../docs/decisions/integration_decisions.md), tài liệu scope/schema/quy tắc chất lượng đã đối chiếu |
| So sánh nguồn phù hợp phạm vi | [So sánh ITviec / TopCV](../../docs/data_collection/source_comparison.md); chỉ tổng hợp bằng chứng trong repo |
| Điều phối từng bước và toàn chuỗi | `src/pipeline/`, [cấu hình](../../config/pipeline.json) |
| Kiểm tra hợp đồng dữ liệu trước/sau module | `src/pipeline/contracts.py` |
| Luồng cleaner → parser → analysis có nhánh RQ1 | [49 kiểm thử tích hợp](../../tests/integration/test_pipeline.py) bằng module giả lập |
| Cách cài đặt, chạy lại parser và API bàn giao | [Hướng dẫn pipeline](../../docs/pipeline/README.md) |
| Đếm bản ghi, trạng thái bước/RQ, nguồn gốc lần chạy | [Bằng chứng fixture](fixture_run.json), [kiểm tra module hiện tại](module_readiness.json) |

Thay đổi được chuẩn bị trong working tree của `main`, chưa commit/push hoặc merge
nhánh của thành viên. Không sao chép hay viết lại logic crawler, cleaner, parser,
RQ1 hoặc thuật toán RQ2–RQ4.

## 2. Kiểm chứng với fixture

Chạy Python 3.11.9 trên môi trường hiện tại:

```powershell
python -m pytest tests/integration -q --basetemp .tmp/pipeline-tests-8 --tb=short
```

Kết quả: **49 passed**. Đường dẫn basetemp này thuộc lần chạy đã ghi nhận; để chạy
lại, bỏ tùy chọn đó hoặc chọn một thư mục mới theo hướng dẫn.

Luồng thành công gọi lần lượt `clean → rq1 → extract → analysis`. Các module giả
lập chỉ chép fixture chuẩn bị sẵn và tạo file kết quả kiểm thử, không tính kết luận
nghiên cứu. Bằng chứng số liệu trong [fixture_run.json](fixture_run.json):

| Mốc | Số bản ghi |
|---|---:|
| Raw | 4 |
| Bảng sạch có cờ, giữ để kiểm toán | 4 |
| Hợp lệ (`relevance=true`, `duplicate=false`) | 2 |
| Duplicate | 1 |
| Ngoài phạm vi | 1 |
| Giao giữa duplicate và ngoài phạm vi | 0 |
| Bảng danh sách kỹ năng | 2 |
| Ma trận job–skill | 2 |

RQ1–RQ4 đều `completed` **ở mức hợp đồng module giả lập**.
`run_kind=integration`, `research_acceptance=false`.

Kiểm thử còn xác nhận: chạy lại extractor/analysis khi không có file raw; bắt lỗi
thiếu trường, sai kiểu boolean, trùng/mất ID, ghi đè trường gốc, thêm trường ngoài
schema, kỹ năng ngoài taxonomy, `skill_count` sai, ô ma trận sai và lệch danh sách;
không dùng lại đầu ra cũ khi module không ghi kết quả; giữ đầu ra cũ khi kiểm tra
đầu ra mới thất bại; phát hiện sửa input; bắt lỗi module và ghi báo cáo; RQ bị bỏ
qua phải có lý do; artifact RQ phải tồn tại trong thư mục đầu ra. Có kiểm tra tin
chỉ có yêu cầu, danh sách kỹ năng rỗng, ngày có kiểu trong Parquet và bảng sạch rỗng.
Kiểm thử schema từ chối các cột lương/học vấn đã bỏ và xác nhận nội dung lương/học
vấn vốn có trong mô tả/yêu cầu vẫn được giữ nguyên.
Kiểm thử kinh nghiệm xác nhận bảo toàn chuỗi nguồn hoặc `null` và từ chối hai
cột số năm phái sinh đã bỏ khỏi schema.

## 3. Kiểm chứng với dữ liệu và module hiện tại

Đọc mẫu trong repo qua validator: **45 bản ghi, đủ 22 trường**, ID duy nhất,
các giá trị bắt buộc và điều kiện văn bản đạt hợp đồng raw. Taxonomy có **246 kỹ năng**,
`skill_id`/`canonical_name` không rỗng và duy nhất. Đây là kiểm tra cấu trúc dữ liệu;
không xác minh lại nội dung với website nguồn và không giải quyết bằng chứng audit
title 19/45 do Dương cung cấp.

Lệnh `python -m src.pipeline --config config/pipeline.json --stage all` trả mã
thoát **1** như dự kiến: cleaner chưa có trên `main`. Báo cáo ghi `raw_records=45`,
bước `clean=failed`; `rq1`, `extract`, `analysis` và RQ1–RQ4 đều `not_run`.
Số bản ghi sạch, kỹ năng và ma trận thực tế chưa có, không thay bằng số fixture.
Xem [module_readiness.json](module_readiness.json).

Không chạy crawl lại. Theo quyết định rút gọn schema, dữ liệu mẫu được chuyển từ
29 sang 22 trường bằng cách bỏ bảy cột toàn `null`: ba cột lương phái sinh, hai
cột kinh nghiệm phái sinh, lương thô và học vấn. Tất cả giá trị còn lại được giữ
nguyên. Hồ sơ chất lượng dữ liệu cũng bỏ hai dòng lương/học vấn không còn trong
schema; các thống kê và nhận xét còn lại được giữ nguyên. Taxonomy không thay đổi.

## 4. Điều kiện còn thiếu cho nghiệm thu chính thức

| Thành viên | Bàn giao/đối chiếu cần hoàn tất | Trạng thái hiện tại |
|---|---|---|
| Đạt | Crawler/dữ liệu cuối, title trung thành với nguồn và metadata thu thập | Có crawler/mẫu 45 tin trên `main`; chưa kiểm chứng đợt dữ liệu cuối |
| Đức | Cleaner tuân thủ 22 trường, giữ ID và trường gốc; API RQ1 cùng quy ước title mới | Cleaner có trên ref `origin/feature/data-cleaner-rq1`, chưa có trên `main`; API RQ1 chưa cấu hình |
| Cường | API extractor, danh sách canonical names, ma trận skill IDs; đánh giá benchmark | Chưa có module thực thi trong repo hiện tại |
| Triều | API RQ2–RQ4, artifact, seed/ngưỡng và trạng thái skip cho dữ liệu thiếu | Có đặc tả; chưa có module thực thi |

Cleaner trên ref hiện tại xuất thêm `quality_flags` và có logic QR-01 bỏ bản ghi.
Cần đối chiếu với quyết định giữ schema 22 trường, log chất lượng riêng và giữ bản
ghi để kiểm toán. Các điểm này được ghi nhận từ việc đọc code của ref, chưa tuyên
bố đã kiểm thử cleaner thật hoặc sửa thay cho Đức.
Cleaner cũng phải ngừng xuất toàn bộ cột lương và học vấn của schema cũ.
Cleaner bỏ bước parse số năm và không xuất hai cột kinh nghiệm phái sinh của schema cũ.

Sau bàn giao: cấu hình entry point thật, dùng dữ liệu chính thức, chạy từng bước,
chạy `all`, lưu báo cáo theo đợt và xác nhận toàn bộ đầu ra RQ. Dương nghiệm thu
chất lượng trích xuất và điều kiện thống kê theo đặc tả; chỉ khi đó mới coi là
nghiệm thu nghiên cứu. Mẫu nhỏ không được dùng để công bố RQ chưa đủ điều kiện.

## 5. Giới hạn khung tích hợp

Pipeline kiểm tra cấu trúc, tính toàn vẹn và artifact, không đánh giá nội dung
thống kê hay chất lượng của thuật toán thành viên. Input được kiểm tra hash trước/
sau module; nếu module vi phạm thì phát hiện và báo lỗi nhưng không tự phục hồi.
Đầu ra được kiểm tra trong thư mục tạm trước khi xuất bản; thao tác xuất nhiều file
không phải giao dịch nguyên tử nếu có lỗi I/O giữa chừng. Báo cáo gần nhất phản ánh
chỉ lần chạy hiện tại; cần lưu riêng báo cáo theo đợt khi nghiệm thu chính thức.
