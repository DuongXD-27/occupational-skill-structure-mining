# Trang duyệt gold kỹ năng (chạy trên máy)

Trang này dùng để duyệt 50 tin gold: quyết định 99 góp ý lượt hai, bỏ nhãn nháp sai,
thêm kỹ năng còn thiếu, và gán độc lập 18 tin nhóm kappa (quyết định F.3). Không cần
tài khoản hay mạng; mọi thứ nằm trong một file HTML.

## Cách dùng

1. `git pull` để có bản mới nhất, rồi mở `tools/gold_review/index.html` bằng Chrome, Edge hoặc Firefox.
2. Gõ tên của bạn vào ô **Người duyệt** ở góc trên.
3. Làm **18 tin có nhãn "nhóm kappa" trước** (lọc bằng nút "Nhóm kappa"):
   - nhãn nháp bị ẩn; bôi đen từng kỹ năng trong văn bản, gõ tìm ở ô bên phải, bấm tên kỹ năng;
   - xong một tin thì bấm **"Xong gán độc lập, mở bản nháp"**, rồi duyệt tiếp như bước 4.
   - Hai người làm 18 tin này **riêng**, không bàn với nhau.
4. Với mỗi tin:
   - mục vàng **"Cần quyết định"**: đọc lý do, chọn Giữ / Thay / Bỏ / Thêm;
   - nhãn nháp không bị góp ý: đúng thì để nguyên, sai thì bấm "Giữ" để chuyển thành "Đã bỏ";
   - còn sót kỹ năng thì bôi đen để thêm; phân vân thì ghi vào ô ghi chú;
   - cuối cùng bấm **"Đánh dấu đã duyệt"**.
5. Kết quả tự lưu trong trình duyệt của máy đó. Cuối mỗi buổi bấm **"Xuất file kết quả"**,
   chép file `gold_review_<tên>.json` vào `data/evaluation/reviews/`, rồi commit và push.
   Đổi máy thì bấm **"Mở file kết quả"** để làm tiếp từ file đã xuất.

Quy tắc thế nào là một kỹ năng: `docs/skill_extraction/annotation_guideline.md` (mục 3–4 và 7–11).

## Sau khi duyệt

```bash
python scripts/merge_gold_reviews.py                  # gộp, tính kappa, ghi xung đột
python scripts/merge_gold_reviews.py --prefer cuong   # nếu muốn lấy theo một người khi khác nhau
python -m src.parser evaluate --gold data/evaluation/gold_jobs.reviewed.jsonl --subset holdout --output-dir reports/skill_extraction/holdout
```

Kết quả gộp: `data/evaluation/gold_jobs.reviewed.jsonl` (gold chính thức),
`review_conflicts.csv` (nhãn hai người quyết định khác nhau, cần thống nhất),
`review_summary.json` (số tin đã duyệt, Cohen's kappa, đồng thuận dương).

## Sửa trang

Sửa `app.js` hoặc `template.html`, rồi chạy `python tools/gold_review/build.py` để dựng lại
`index.html` từ gold nháp, góp ý lượt hai và taxonomy.
