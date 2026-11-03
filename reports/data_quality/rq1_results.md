# Kết quả RQ1 — Chức danh công việc

> **RQ1:** Những chức danh nào tồn tại và mỗi chức danh phổ biến ra sao?
> Sinh tự động bởi `scripts/report_cleaning.py` (module `src/cleaner/rq1.py`);
> bảng và biểu đồ đầy đủ ở `reports/analysis/rq1/`.

**Tập phân tích:** 211 tin (`relevance_flag=true` VÀ `duplicate_flag=false`), cùng con số với báo cáo chất lượng.

> ⚠️ Dưới 1.000 tin: đây là kiểm thử pipeline trên tập pilot, chưa phải phát hiện nghiên cứu
> (analysis_spec §8).

## Bảng tổng hợp

| Chỉ số | Giá trị | Ý nghĩa |
|---|---|---|
| `n_postings` | 211 | Số tin hợp lệ (relevance=true, duplicate=false) |
| `n_raw_titles` | 206 | Số chức danh thô khác biệt (trim + lowercase) |
| `n_normalized_titles` | 189 | Số chức danh chuẩn hóa khác biệt |
| `compression_ratio` | 0.9175 | Số chức danh chuẩn hóa ÷ số chức danh thô |
| `top1_share` | 0.0332 | Tỷ trọng tin của chức danh phổ biến nhất |
| `top5_share` | 0.1137 | Tỷ trọng tin của 5 chức danh phổ biến nhất |
| `top10_share` | 0.1517 | Tỷ trọng tin của 10 chức danh phổ biến nhất |
| `hhi` | 0.0073 | Herfindahl–Hirschman trên tỷ trọng chức danh chuẩn hóa |
| `entropy_raw_bits` | 7.6566 | Entropy Shannon của chức danh thô |
| `entropy_normalized_bits` | 7.4205 | Entropy Shannon của chức danh chuẩn hóa |
| `entropy_normalized_ratio` | 0.9813 | Entropy chuẩn hóa ÷ log2(số chức danh); 1 = phân bổ đều |
| `n_rare_titles` | 185 | Số chức danh chuẩn hóa có ≤ 2 tin |
| `rare_title_share` | 0.9788 | Tỷ lệ chức danh hiếm trên tổng số chức danh chuẩn hóa |
| `rare_posting_share` | 0.8957 | Tỷ lệ tin thuộc chức danh hiếm |
| `n_companies_behind_rare` | 136 | Số công ty đăng các chức danh hiếm |
| `top3_company_share_of_rare` | 0.1111 | Tỷ trọng tin hiếm đến từ 3 công ty đăng nhiều nhất |
| `sample_note` | pipeline_test | Dưới 1000 tin: chỉ là kiểm thử pipeline, không phải phát hiện nghiên cứu |

## Top 20 chức danh chuẩn hóa

| Hạng | Chức danh chuẩn hóa | Số tin | Tỷ trọng |
|---|---|---|---|
| 1 | Business Analyst | 7 | 3.3% |
| 2 | Data Engineer | 6 | 2.8% |
| 3 | AI Engineer | 6 | 2.8% |
| 4 | Machine Learning Engineer | 3 | 1.4% |
| 5 | Data Analyst | 2 | 0.9% |
| 6 | IT Business Analyst | 2 | 0.9% |
| 7 | Technical Business Analyst | 2 | 0.9% |
| 8 | Fullstack Engineer | 2 | 0.9% |
| 9 | Data Analyst (CRM & Loyalty) | 1 | 0.5% |
| 10 | Product Data Analyst | 1 | 0.5% |
| 11 | Head of Enterprise Data (AI/Database/Data Science) | 1 | 0.5% |
| 12 | Business Analyst / Data Analyst | 1 | 0.5% |
| 13 | Data & Business Intelligence Professional / Senior Prof | 1 | 0.5% |
| 14 | Internship - BA | 1 | 0.5% |
| 15 | Business Intelligence Analyst (Financial Services) | 1 | 0.5% |
| 16 | Data Manager (Data Analytics, Business Intelligence) | 1 | 0.5% |
| 17 | AI Engineer (Computer Vision/NLP/LLM) | 1 | 0.5% |
| 18 | AI Data Engineer | 1 | 0.5% |
| 19 | Data Engineer (C++, Python, AI/LLM) | 1 | 0.5% |
| 20 | Chuyên Gia Tích Hợp Dữ Liệu (Data Engineer Expert) | 1 | 0.5% |

Danh sách 185 chức danh hiếm (≤ 2 tin) kèm công ty và URL: `reports/analysis/rq1/rq1_rare_titles.csv`.
