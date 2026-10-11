# Báo cáo thử nghiệm bộ trích xuất kỹ năng

Ngày chạy: 2026-10-11. Thuật toán và vocabulary được cố định cho lần đánh giá;
không bổ sung alias hoặc chỉnh nhãn để tăng điểm sau khi xem predictions.

## Kết quả trên gold dự thảo 50 tin

Nguồn: 252 tin pilot ITviec trên nhánh crawler, chọn 50 tin độc lập với mẫu xây
taxonomy. Codex đọc văn bản và gán **634 nhãn** với bằng chứng/offset trước khi
chạy predictions. Đây là **gold dự thảo do trợ lý gán nhãn, chưa được người rà
soát độc lập nghiệm thu**. Xem [phương pháp và giới hạn lấy mẫu](../../data/evaluation/README.md).

| Chỉ số micro theo cặp job–skill | Kết quả |
|---|---:|
| True positive (TP) | 541 |
| False positive (FP) | 21 |
| False negative (FN) | 93 |
| Precision = TP / (TP + FP) | 96,26% |
| Recall = TP / (TP + FN) | 85,33% |
| F1 = 2TP / (2TP + FP + FN) | 90,47% |
| Tin có ít nhất một FP hoặc FN | 43 / 50 |

634 = TP + FN; 562 nhãn dự đoán = TP + FP. Tính theo tập nhãn từng tin, không tính
lặp một kỹ năng nhiều lần trong cùng tin. Trường hợp mẫu số bằng 0 dùng 0.
Các số này đo độ khớp với nhãn dự thảo trong taxonomy 246 kỹ năng, chưa phải đánh
giá bằng gold do người gán nhãn độc lập hoặc độ bao phủ các công nghệ ngoài taxonomy.

Artifact tái lập: [metrics.json](draft_gold/metrics.json),
[errors.jsonl](draft_gold/errors.jsonl), [per_skill.csv](draft_gold/per_skill.csv),
[predictions.jsonl](draft_gold/predictions.jsonl).
`human_reviewed=false`, `research_acceptance=false`.

## Các nhóm lỗi đã quan sát

| Nhóm | Ví dụ có trong dữ liệu | Hướng xử lý sau rà soát |
|---|---|---|
| Thiếu alias, dạng số ít/số nhiều, hoa/thường | `Database` không khớp `Databases`; `Oracle`, `MS SQL`, `Big Query`, `vector databases`, `K8S` | Bổ sung alias qua quy trình taxonomy, giữ nguyên skill IDs |
| Thiếu bản dịch/tác vụ tiếng Việt | “bảo mật dữ liệu”, “học máy”, “triển khai mô hình” | Đối chiếu nhãn và thêm biến thể được phê duyệt |
| Tên trùng từ thông dụng hoặc ngữ cảnh khác | `React` khớp `ReAct`; `C.` là đề mục; `fine-tuning` database khớp Fine-Tuning của ML; HA `Clustering` | Quy tắc ngữ cảnh theo từng thuật ngữ, kiểm thử trước thay đổi |
| Vùng văn bản không phải yêu cầu kỹ năng | ngành học `Statistics`; CI/CD/cloud ở giới thiệu công ty; CRM mô tả sản phẩm | Crawler/cleaner cần tách vùng nội dung; parser hiện nhận toàn bộ text |
| Ranh giới khái niệm và nhãn dự thảo | `Optimization`, `System Architecture`, `Reporting`, Computer Vision từ facial recognition | Người rà soát quyết định theo hướng dẫn; không tự coi mọi lỗi là lỗi parser |

FN nhiều nhất: `Databases` 11, `Oracle Database` 7, `Data Security` 6,
`Automation Engineering` 5, `Model Deployment` 4. Danh sách từng tin được giữ để
rà soát, không che các nhóm khó hoặc chọn lại mẫu dựa trên lỗi parser.

Chưa có ví dụ phủ định rõ trong gold này. Bộ hồi quy giữ ba giới hạn chưa sửa
bằng `xfail(strict=True)`: `Python is not required`, `Go to the office`, và lời
mời gửi CV trong cùng tài liệu có OpenCV. Matcher CV đang dùng ngữ cảnh toàn tài
liệu; C/R/Go dùng phân biệt hoa/thường và bảo vệ boundary, chưa đủ để giải quyết
tất cả ngữ cảnh. Không suy ra độ chính xác phủ định từ F1 ở trên.

`OpenCV`, Hugging Face và các công nghệ mới chỉ được ghi vào
[taxonomy_gaps.csv](taxonomy_gaps.csv) cùng bằng chứng từ pilot. Chưa thêm chúng
vào taxonomy đã đóng băng; không đưa nhãn ngoài vocabulary vào TP/FP/FN. Vì vậy
với taxonomy mặc định, “Computer vision experience with OpenCV” chỉ trả
`Computer Vision`. Test riêng xác nhận thêm OpenCV qua taxonomy là đủ để parser
trả cả hai, không cần thêm vocabulary trong code.

## Kiểm tra ngay trên 45 tin hiện có

Đã chạy cùng thuật toán trên 45 tin raw, xuất
[sample_job_skills.parquet](../../data/features/development/sample_job_skills.parquet)
và [sample_job_skill_matrix.parquet](../../data/features/development/sample_job_skill_matrix.parquet),
cùng [manifest](../../data/features/development/sample_manifest.json).
Cả hai bảng có 45 dòng; ma trận có `job_id` + 246 cột skill IDs, giá trị 0/1;
danh sách canonical names và từng ô ma trận khớp. Preview giữ cả tin duplicate/
ngoài phạm vi chưa được cleaner đánh cờ, chỉ dùng kiểm tra thuật toán.

Trong lúc tách matcher, sửa lỗi khử trùng skill trước khi kiểm tra tất cả các
span overlap: lần thứ hai của cùng cụm dài bị bỏ qua, để thuật ngữ ngắn bên
trong bị đếm thừa. Giờ kiểm tra toàn bộ span trước rồi khử trùng theo skill ID.
`SQL Server, SQL Server` chỉ tạo Microsoft SQL Server; SQL độc lập vẫn được giữ
nếu có một đề cập ngoài cụm đó.

Đối chiếu với matcher trên main cho thấy chỉ ba document counts thay đổi:

| Kỹ năng | Trước | Sau |
|---|---:|---:|
| BigQuery | 7 | 6 |
| Caching | 2 | 1 |
| Claude | 5 | 4 |

Bằng chứng tin bị ảnh hưởng ở [overlap_corrections.csv](overlap_corrections.csv).
Taxonomy giữ nguyên 246 skill IDs/names/alias/groups; chỉ cập nhật ba
`observed_count`. Số kỹ năng xuất hiện một lần đổi 102 → 103; 150 kỹ năng vẫn có
count tối đa 2. Recount kiểm tra lại cùng parser và đủ 45 tin. Đây là document
frequency trong mẫu taxonomy, không phải số liệu nhu cầu trên gold/ thị trường.

## Bàn giao và điều kiện còn thiếu

Module Python, CLI, entry point pipeline, evaluator, unit tests, gold dự thảo và
báo cáo đã có. Kiểm thử xác nhận alias/overlap/abbreviation/C/R/Go/CV, parity
recount, lọc cờ, danh sách rỗng, ma trận và bảo toàn input/đầu ra cũ khi dữ liệu sai.

`python -m pytest tests/parser -q`: **53 passed, 3 xfailed** (ba giới hạn đã biết
nêu trên). `python scripts/recount_taxonomy.py --check` thành công. Đã chạy parser
thật trong chuỗi của snapshot PR #15 với cleaner/RQ giả lập: hai tin raw, một tin
duplicate, một tin hợp lệ, một dòng skills/matrix, `research_acceptance=false`.
Bằng chứng ở [pipeline_compatibility.json](pipeline_compatibility.json); không
merge hoặc tuyên bố đã kiểm thử cleaner/thuật toán RQ thật của thành viên.

Hai artifact **chính thức** `data/features/job_skills.parquet` và
`data/features/job_skill_matrix.parquet` chờ Đức bàn giao clean được nghiệm thu.
Không dùng file clean đang trên nhánh thành viên như dữ liệu chính thức và không
merge nhánh đó trong PR này. Lệnh extract/API đã sẵn sàng, lọc
`relevance_flag=true AND duplicate_flag=false`; Triều nhận cả hai file cùng
manifest sau lần chạy clean cuối. Xem [hướng dẫn chạy](../../docs/skill_extraction/parser.md).

Gold cần người rà soát các nhãn hiện có, phần bị bỏ sót và đề xuất mở rộng
taxonomy. Sau khi đóng băng nhãn/vocabulary được duyệt, chạy đánh giá lại; nếu
sửa thuật toán theo lỗi của tập này thì cần tập kiểm thử mới cho đánh giá cuối.
