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

## Tái lập mẫu chờ gán nhãn

Đọc snapshot pilot từ Git vào một file UTF-8, sau đó chạy:

```powershell
python scripts/prepare_skill_gold.py --input <pilot.jsonl> --output .tmp/gold_pending.jsonl --limit 50
python -m src.parser evaluate --gold data/evaluation/gold_jobs.draft.jsonl --output-dir reports/skill_extraction/draft_gold
```

Lệnh prepare chỉ chọn mẫu và để nhãn trống. Evaluator từ chối tập chưa gán nhãn,
ID/URL trùng, cặp gần trùng, canonical name/skill ID sai hoặc đoạn bằng chứng sai.
