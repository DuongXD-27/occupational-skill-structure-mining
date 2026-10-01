# Báo cáo chất lượng dữ liệu — Tập pilot

> Nguồn: `data/pilot/jobs_pilot.jsonl` (parser v0.2, nguồn: ITviec)

## 1. Tóm tắt pipeline (Trước / Sau)

| Chỉ số | Trước khi làm sạch | Sau khi làm sạch |
|---|---|---|
| Tổng bản ghi đầu vào | 252 | 252 |
| Loại bỏ (QR-01: lỗi crawl / trống) | — | 0 |
| Ngoài phạm vi (`relevance_flag=false`) | — | 34 (13.5%) |
| Trùng lặp (`duplicate_flag=true`) | — | 26 (10.3%) |
| **Bản ghi sạch (liên quan + không trùng)** | — | **192** |

## 2. Tỉ lệ thiếu dữ liệu (Trước / Sau)

| Trường | Thiếu trước | Thiếu sau | Thay đổi |
|---|---|---|---|
| `normalized_location` | 252 (100%) | 98 (38.9%) | -154 bản ghi đã chuẩn hoá |
| `experience_min_years` | 252 (100.0%) | 252 (100.0%) | xem ghi chú |
| `normalized_job_title` | 252 (100%) | 0 (0.0%) | -252 bản ghi đã chuẩn hoá |

## 3. Kết quả chuẩn hoá

| Chỉ số | Số lượng |
|---|---|
| Số chức danh chuẩn hoá khác nhau | 246 |
| Số địa điểm chuẩn hoá khác nhau | 3 |

## 4. Cờ chất lượng (Quality Flags)

| Cờ | Số lượng |
|---|---|
| `MISSING_EXPERIENCE` | 252 |
| `MISSING_LOCATION` | 83 |
| `MANUAL_REVIEW_REQUIRED` | 48 |
| `DUPLICATE_NEAR` | 26 |
| `LOCATION_UNRECOGNIZED` | 18 |
| `MULTI_LOCATION` | 6 |
| `AMBIGUOUS_CLASSIFICATION` | 6 |
| `AMBIGUOUS_TITLE` | 5 |

## 5. Ghi chú

> **QR-03 (Kinh nghiệm):** Trường `raw_experience` trống hoàn toàn trong parser v0.2.
> `experience_min_years` giữ nguyên null cho đến khi crawler được cập nhật.
> Tất cả bản ghi được gắn cờ `MISSING_EXPERIENCE`. Đây là giới hạn từ upstream,
> không phải lỗi của cleaner.

> **QR-05 (Trùng lặp):** Phát hiện trùng gần dựa trên độ tương đồng TF-IDF cosine
> trên `job_description` (ngưỡng 0.80) kết hợp khớp tên công ty.
> Trùng chính xác dựa trên `source_url` giống nhau.