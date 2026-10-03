# Kết quả phân tích RQ2–RQ4

**Owner:** Hồ Nhật Triều (20236003)

---

## Số trong thư mục này là từ DỮ LIỆU GIẢ

Bước bóc skill chưa bàn giao artifact: `extracted_skills` null trên cả 45 tin
trong `data/sample/sample_jobs.jsonl`, và `data/features/` chưa tồn tại.

Nên mọi bảng và hình ở đây sinh ra từ `src/analysis/synthetic.py` — 400 tin
giả, 4 nghề gieo sẵn.

**Mục đích: chứng minh code chạy đúng, không phải mô tả thị trường.**
Không trích số nào từ đây vào báo cáo.

Task mục 5 cho phép dùng dữ liệu giả để kiểm tra thuật toán. Mục 7 yêu cầu
kết quả chính thức phải chạy lại trên artifact cuối của bước làm sạch và
bước bóc skill — việc đó chưa làm được.

## Tạo lại

```
python scripts/run_analysis.py            # dữ liệu giả (hiện tại)
python scripts/run_analysis.py --real     # khi có dữ liệu thật
```

## Các file

| File | Nội dung | Task mục 6 |
|---|---|---|
| `rq2_skill_frequency.csv` | Mỗi skill có trong bao nhiêu tin | bảng tần suất skill |
| `rq2_skill_pairs.csv` | Cặp skill kèm Lift, NPMI, Jaccard | bảng cặp skill |
| `rq2_skill_communities.csv` | Nhóm skill tự hình thành | community artifact |
| `rq2_skills_per_posting.csv` | Số skill trung bình mỗi tin | kiểm tra bộ bóc skill |
| `rq3_title_dispersion.csv` | Phân tán skill trong cùng title, kèm mốc ngẫu nhiên | phân tán + bootstrap baseline |
| `rq3_title_similarity.csv` | Cosine giữa hồ sơ các title | title có profile gần nhau |
| `rq3_notable_pairs.csv` | Cặp title đáng chú ý, skill chung và skill phân biệt | bảng minh họa |
| `rq3_skipped_titles.csv` | Title bị bỏ vì dưới 5 tin | — |
| `rq4_k_sweep.csv` | Silhouette, Davies-Bouldin, stability theo từng k | quét k + 3 chỉ số |
| `rq4_cluster_profiles.csv` | Mỗi cụm gồm skill gì | — |
| `rq4_cluster_assignment.csv` | Mỗi tin thuộc cụm nào | cluster assignment |
| `rq4_clusters_with_titles.csv` | Cụm + skill + title sau khi unblind | bảng title trong từng cluster |
| `rq4_agreement.csv` | ARI và NMI giữa cụm và title | — |
| `rq4_pca_coordinates.csv` | Toạ độ 2 chiều để vẽ | — |
| `rq4_pca.png` | Hai khung PCA cạnh nhau: theo cụm và theo title | PCA visualization |
| `rq4_sweep_k.png` | Ba chỉ số theo từng k | — |

`sample_analysis_check.md` là báo cáo kiểm tra dữ liệu mẫu, thuộc giai đoạn
trước, không liên quan tới các file trên.
