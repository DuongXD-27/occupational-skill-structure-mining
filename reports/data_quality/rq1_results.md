# Kết quả phân tích RQ1 — Chuẩn hoá chức danh công việc

> **RQ1:** Có bao nhiêu chức danh chuẩn hoá khác nhau trong thị trường Data/AI?

**Tập phân tích:** 193 bản ghi (liên quan + không trùng lặp)

## Thống kê chức danh

| Chỉ số | Thô | Chuẩn hoá |
|---|---|---|
| Số chức danh khác nhau | 188 | 188 |
| Shannon entropy (bits) | 7.522 | 7.522 |
| Tỉ lệ nén | — | 0.0% |
| Chức danh xuất hiện 1 lần | 186 | 186 |

## Top 10 chức danh chuẩn hoá

| Hạng | Chức danh chuẩn hoá | Số lượng |
|---|---|---|
| 1 | AI Engineer | 5 |
| 2 | Business Analyst | 2 |
| 3 | Senior Data Analyst Crm & Loyalty | 1 |
| 4 | Senior Product Data Analyst SQL/Python/R | 1 |
| 5 | Data Analyst Bi, Power Bi, Sql, Data Warehouse, ETL | 1 |
| 6 | Data Analyst Azure, Sql, NoSQL, Power BI | 1 |
| 7 | Head of Enterprise Data AI/Database/Data Science | 1 |
| 8 | Business Analyst/ Data Analyst | 1 |
| 9 | Data & Business Intelligence Professional / Senior Prof | 1 |
| 10 | Internship - BA | 1 |

## Phân bố tần suất

| Tần suất | Số chức danh chuẩn hoá |
|---|---|
| 5 | 1 |
| 2 | 1 |
| 1 | 186 |

## Ghi chú

> **QR-03 (Kinh nghiệm):** Trường `raw_experience` trống trong toàn bộ dữ liệu parser v0.2.
> `experience_min_years` / `experience_max_years` giữ nguyên null.
> Đây là giới hạn từ upstream; cleaner xử lý an toàn với cờ `MISSING_EXPERIENCE`.

> **Định nghĩa tập phân tích:** Chỉ tính các bản ghi có `relevance_flag=true` VÀ
> `duplicate_flag=false` vào RQ1, tránh đếm tin ngoài phạm vi hoặc tin trùng
> như một nhu cầu tuyển dụng độc lập.