# Báo cáo chất lượng dữ liệu — Tập pilot

> Nguồn: `data/pilot/jobs_pilot.jsonl` (parser v0.2, nguồn: ITviec).
> Sinh tự động bởi `scripts/report_cleaning.py`; cùng lần chạy với `rq1_results.md`.

## 1. Tóm tắt pipeline

| Chỉ số | Số lượng |
|---|---|
| Tổng bản ghi đầu vào | 252 |
| Bản ghi trong bảng sạch (không xóa bản ghi nào) | 252 |
| Lỗi kỹ thuật QR-01 (`exclusion_reason=SCRAPE_ERROR`) | 0 |
| Ngoài phạm vi (`relevance_flag=false`) | 36 (14.3%) |
| Trùng lặp (`duplicate_flag=true`) | 5 (2.0%) |
| Vừa ngoài phạm vi vừa trùng lặp (tính một lần) | 0 |
| **Tin hợp lệ (`relevance=true AND duplicate=false`)** | **211** |

Lý do loại trừ:

| `exclusion_reason` | Số lượng |
|---|---|
| `NOT_DATA_AI_ROLE` | 36 |

## 2. Kết quả chuẩn hóa

| Trường | Có giá trị | Thiếu |
|---|---|---|
| `normalized_job_title` | 252 | 0 |
| `normalized_location` | 154 | 98 |
| `job_text` | 252 | 0 |

- Số chức danh thô khác biệt (trim + lowercase, toàn bảng): 246
- Số chức danh chuẩn hóa khác biệt (toàn bảng): 229
- Số địa điểm chuẩn hóa khác biệt: 3

## 3. Cờ chất lượng

Cờ không thuộc schema 22 trường nên được ghi ở file riêng `data/processed/pilot/jobs_clean_pilot.quality_flags.jsonl`.

| Cờ | Số lượng |
|---|---|
| `MISSING_EXPERIENCE` | 252 |
| `MISSING_LOCATION` | 83 |
| `SENIORITY_REMOVED` | 74 |
| `MANUAL_REVIEW_REQUIRED` | 47 |
| `LOCATION_UNRECOGNIZED` | 18 |
| `TECH_SUFFIX_REMOVED` | 13 |
| `MULTI_LOCATION` | 6 |
| `AMBIGUOUS_CLASSIFICATION` | 6 |
| `AMBIGUOUS_TITLE` | 5 |
| `DUPLICATE_NEAR` | 5 |

## 4. Ghi chú

> **QR-03 (Kinh nghiệm):** Theo quyết định 2026-10-04, chỉ giữ `raw_experience` nguyên văn;
> cleaner không parse số năm. Bản ghi thiếu dữ liệu nguồn mang cờ `MISSING_EXPERIENCE`;
> giá trị hình thức làm việc bị crawler gán nhầm mang thêm `SCRAPER_FIELD_MISMATCH`.

> **QR-04 (Chức danh):** Bỏ cấp bậc thuần túy (Senior/Junior/Middle/Fresher) và hậu tố
> công nghệ rõ ràng (mọi mục đều là công cụ trong taxonomy) theo quyết định 2026-10-03 §C.
> Phần trong ngoặc mô tả chuyên môn/lĩnh vực được giữ. Cờ `SENIORITY_REMOVED`,
> `TECH_SUFFIX_REMOVED` ghi lại phần đã bỏ để kiểm toán.

> **QR-05 (Trùng lặp):** Trùng chính xác khi cùng `source_url`. Trùng gần khi đồng thời khớp
> `company`, độ tương đồng Jaccard của `normalized_job_title` ≥ 0.60, khớp
> `normalized_location`, và TF-IDF cosine trên `job_description` ≥ 0.80. Luồng JD-only
> (cosine ≥ 0.95) vẫn là đề xuất chờ Leader duyệt nên tắt mặc định.
