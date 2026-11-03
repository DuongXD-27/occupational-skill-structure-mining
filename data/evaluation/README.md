# Gold dự thảo cho skill parser

[gold_jobs.draft.jsonl](gold_jobs.draft.jsonl) chứa **50 tin thực từ pilot ITviec**,
634 nhãn thuộc taxonomy hiện có và đoạn bằng chứng cho từng nhãn. Nguồn là snapshot
`origin/feature/data-collection-sample` tại commit
`8d4749d61599b8cac8107e74f80e5ca69ca80ddd`, file `data/pilot/jobs_pilot.jsonl` (252 tin).
Không crawl lại hoặc sửa dữ liệu của Đạt. Metadata/hash ở [manifest.json](manifest.json).

Theo yêu cầu chuẩn bị khoảng 50 tin, Codex đã đọc từng văn bản và gán nhãn dự thảo
trước khi chạy dự đoán parser trên tập này. Nhãn không được lấy từ output parser.
**Đây là nhãn do trợ lý gán, chưa phải gold đã được người gán nhãn/rà soát độc lập
nghiệm thu.** Tất cả bản ghi có `annotation_status=assistant_annotated_draft`,
`annotated_by=Codex`, `human_reviewed=false`; kết quả đánh giá vẫn là thử nghiệm.

## Chọn mẫu và giới hạn

Loại tin trùng `job_id`, `source_url` hoặc `source_job_id` với 45 tin dùng xây taxonomy
và với các tin đã chọn. So sánh Jaccard tập cụm 5 từ từ mô tả/yêu cầu, loại cặp có
độ tương đồng từ 0,5 trở lên. Kiểm tra này giảm trùng văn bản, không chứng minh mọi
bản đăng lại/biến thể đều đã được loại.

Lọc title có Data, AI, Machine Learning hoặc Business Intelligence; lấy 50 tin
ngắn nhất theo độ dài văn bản, hòa thì theo `job_id`. Cách lấy này thuận tiện cho
gán nhãn nhưng thiên về JD ngắn; có cả vai trò phần mềm, quản trị DB, sản phẩm và
tư vấn. Đây là tập kiểm tra bộ trích xuất trên tin ứng viên từ crawler, chưa phải
tập Data/AI đã qua cleaner để kết luận nhu cầu thị trường.

Vùng gán nhãn: mô tả, yêu cầu/điểm cộng và công nghệ rõ ràng trong title. Loại phần
giới thiệu công ty, ngành học, nội dung tuyển dụng chung và chức danh nghề nghiệp
thuần túy theo [hướng dẫn](../../docs/skill_extraction/annotation_guideline.md).
Tên công cụ/phương pháp rõ ràng được ánh xạ về canonical names, gồm bản dịch như
“cơ sở dữ liệu” → `Databases`, “học máy” → `Machine Learning`. Không suy diễn Docker
từ Kubernetes hoặc Computer Vision chỉ từ tên thư viện OpenCV. Các cách dịch,
thuật ngữ chung và ranh giới kỹ năng/tác vụ cần được người rà soát quyết định lại.

## Rà soát

Mở [review_queue.csv](review_queue.csv), đọc văn bản đầy đủ qua `job_id` trong JSONL
và đối chiếu từng đoạn bằng chứng. CSV chỉ hỗ trợ rà soát; cập nhật nhãn cuối vào
JSONL, gồm `gold_skills`, `annotations`, `skill_id` và offset đúng trên trường `text`.
Thêm/xóa nhãn có lý do theo hướng dẫn, kiểm tra cả nhãn bị bỏ sót. Ghi tên người
rà soát vào `annotated_by` và đổi `annotation_status=human_reviewed`,
`human_reviewed=true` sau khi hoàn tất tin đó. Lưu phiên bản mới thay vì sửa bản
dự thảo đã dùng cho báo cáo. Không điều chỉnh nhãn chỉ để khớp output parser.

`OpenCV`, Hugging Face/Transformers và nhiều công cụ trong pilot chưa có trong
taxonomy 246 kỹ năng. Các đề xuất và bằng chứng ở
[taxonomy_gaps.csv](../../reports/skill_extraction/taxonomy_gaps.csv).
Chúng không được thêm lén vào parser hoặc tính vào TP/FN của đánh giá canonical
hiện tại; chỉ số này không đo khả năng bao phủ mọi công nghệ ngoài taxonomy.

## Rà soát lượt hai (trợ lý AI, 2026-11-03)

[review_pass2.jsonl](review_pass2.jsonl) là góp ý của Claude sau khi đọc lại cả 50 tin theo
[hướng dẫn gán nhãn](../../docs/skill_extraction/annotation_guideline.md). File **không sửa**
`gold_jobs.draft.jsonl` và **không thay thế người duyệt**: mọi dòng có `human_reviewed=false`.

- `kind=label`: nhãn gold đáng ngờ. `action=sửa bằng chứng` khi kỹ năng đúng nhưng đoạn bằng
  chứng trỏ sai chỗ (ví dụ chữ «SQL» nằm trong «MSSQL», «học máy» nằm trong «khoa học máy tính»);
  `thay` khi nên đổi sang kỹ năng khác; `xem` khi cần người quyết theo hướng dẫn.
- `kind=missing`: kỹ năng có trong văn bản nhưng gold chưa gán, kèm offset đề xuất.
- `level=cao`: gần như chắc chắn theo hướng dẫn; `level=xem`: cần người quyết.

Tổng cộng 99 góp ý: 24 nhãn đáng ngờ (12 sửa bằng chứng, 1 thay, 11 cần xem) và 75 nhãn
có thể bị sót (25 mức cao, 50 cần xem). Nếu chấp nhận toàn bộ góp ý mức cao, gold có 659
nhãn và parser hiện tại đạt Precision 96,1%, Recall 81,9%, F1 88,5% (so với 96,3% / 85,3% /
90,5% trên bản nháp). Phần lớn nhãn bị sót cũng là chỗ parser bỏ sót, nên bản nháp đang làm
Recall trông cao hơn thực tế.

## Chia tune / holdout (quyết định 2026-11-03, F.9)

Gold được chia cố định theo `job_id` (băm `sha256("gold-split-v1:" + job_id)`, chẵn →
`holdout`). Với 50 tin hiện tại: 27 tin `tune`, 23 tin `holdout`; tin thêm sau không làm
đổi nhóm của tin cũ.

- Chỉ xem lỗi trên nửa `tune` khi bổ sung alias hoặc chỉnh parser.
- Không mở `errors.jsonl`/`predictions.jsonl` của nửa `holdout` trước ngày khóa
  taxonomy/parser (2026-11-23).
- P/R/F1 chính thức báo cáo trên `holdout`, sau khi gold đã được người duyệt:

```powershell
python -m src.parser evaluate --gold <gold đã duyệt>.jsonl --output-dir reports/skill_extraction/holdout --subset holdout
```

## Tái lập mẫu chờ gán nhãn

Đọc snapshot pilot từ Git vào một file UTF-8, sau đó chạy:

```powershell
python scripts/prepare_skill_gold.py --input <pilot.jsonl> --output .tmp/gold_pending.jsonl --limit 50
python -m src.parser evaluate --gold data/evaluation/gold_jobs.draft.jsonl --output-dir reports/skill_extraction/draft_gold
```

Lệnh prepare chỉ chọn mẫu và để nhãn trống. Evaluator từ chối tập chưa gán nhãn,
ID/URL trùng, cặp gần trùng, canonical name/skill ID sai hoặc đoạn bằng chứng sai.

## Trang duyệt (2026-11-03)

Duyệt trên trang "Duyệt gold kỹ năng" (artifact riêng tư của Dương; chia sẻ cho người duyệt
với quyền Contributor). Mỗi người duyệt có một bản lưu riêng; trang xuất `gold_reviewed_<ngày>.jsonl`
(chỉ các tin đã đánh dấu duyệt xong) với `gold_skills`, `annotations` (offset trên trường `text`),
`human_reviewed=true`, quyết định cho từng góp ý lượt hai và ghi chú.

**Nhóm kappa (quyết định F.3):** 18 tin cố định, lấy 18 `job_id` đầu tiên khi sắp xếp theo
`sha256("kappa-v1:" + job_id)`. Với các tin này, nhãn nháp bị ẩn cho đến khi người duyệt gán độc lập
xong; trang tính Cohen's kappa (trên mọi cặp tin × 246 kỹ năng taxonomy) và đồng thuận dương giữa
từng cặp người duyệt.
