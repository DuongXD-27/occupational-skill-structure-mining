# RQ4 — LÀM TAY TRƯỚC, ĐỌC CODE SAU

Cầm giấy bút. Làm hết phần A rồi mới xem phần B.

RQ4 hỏi: **giấu hết tên công việc đi, dữ liệu tự chia thành mấy nhóm nghề?**

Đây là câu chính của cả đồ án.

---
---

# PHẦN A — TÍNH TAY

## Dữ liệu

Sáu tin. **Tên công việc bị che đi** — anh chưa được biết.

```
job_1:  Python, PyTorch, OpenCV
job_2:  Python, PyTorch, YOLO
job_3:  PyTorch, OpenCV, YOLO
job_4:  SQL, Power BI, Excel
job_5:  SQL, Power BI, Tableau
job_6:  SQL, Excel, Tableau
```

---

# CHIỀU 1 — GOM NHÓM KHI KHÔNG BIẾT TÊN NGHỀ

## Bước 1 — Tự gom bằng mắt

Chỉ nhìn skill. Chia 6 tin thành 2 nhóm:

```
Nhóm 1: ________________
Nhóm 2: ________________
```

Dựa vào đâu mà chia? Viết ra giấy.

## Bước 2 — Giờ mới mở tên công việc ra

```
job_1:  Computer Vision Engineer
job_2:  Computer Vision Engineer
job_3:  Computer Vision Engineer
job_4:  Data Analyst
job_5:  Data Analyst
job_6:  Data Analyst
```

Nhóm anh chia có trùng với tên nghề không? ____

**Chú ý thứ tự: gom trước, mở tên sau.** Nếu biết tên trước rồi mới gom thì
chẳng chứng minh được gì — anh chỉ đang chép lại cái tên.

Đây là lý do `rq4.py` không bao giờ cho title vào ma trận, và chỉ ghép title
lại sau khi cụm đã chốt.

---

# CHIỀU 2 — LÀM SAO BIẾT CÁCH CHIA NÀY ĐÁNG TIN?

Chia được không có nghĩa là chia đúng. Máy luôn chia được, kể cả khi dữ liệu
chẳng có cấu trúc gì.

Cách kiểm tra: **đổi dữ liệu một chút, chia lại, xem kết quả có giống không.**

## Bước 3 — Hai mẫu chồng lấn

Bỏ bớt mỗi mẫu một tin:

```
Mẫu A:  job_1  job_2  job_3  job_4  job_5          (bỏ job_6)
Mẫu B:         job_2  job_3  job_4  job_5  job_6   (bỏ job_1)
```

Gom mỗi mẫu thành 2 nhóm, như bước 1:

```
Mẫu A — nhóm 1: ____________   nhóm 2: ____________
Mẫu B — nhóm 1: ____________   nhóm 2: ____________
```

## Bước 4 — Máy đặt tên nhóm là số, và nó đặt tùy tiện

Đây là kết quả thật của máy. Để ý kỹ:

```
Mẫu A:   job_1 → 0    job_2 → 0    job_3 → 0    job_4 → 1    job_5 → 1
Mẫu B:                job_2 → 1    job_3 → 1    job_4 → 0    job_5 → 0
```

Hai lần chạy chia **giống hệt nhau**, nhưng máy gọi nhóm Computer Vision là
`0` ở lần A và `1` ở lần B.

Giờ thử so theo nhãn. Chỉ xét 4 tin có mặt ở cả hai mẫu:

```
         A     B    trùng nhãn?
job_2    0     1       ____
job_3    0     1       ____
job_4    1     0       ____
job_5    1     0       ____

Số tin trùng nhãn: ____ / 4
```

**Kết luận gì về cách so này?**

## Bước 5 — Cách so đúng: hỏi theo từng CẶP

Đừng hỏi "tin này nhãn mấy". Hỏi:

> Hai tin này có bị xếp **chung nhóm** không?

Câu hỏi đó không quan tâm nhóm tên là gì.

Bốn tin cho 6 cặp. Điền `chung` hoặc `khác`:

```
            ở mẫu A     ở mẫu B     khớp?
job_2-job_3   _____       _____      ____
job_2-job_4   _____       _____      ____
job_2-job_5   _____       _____      ____
job_3-job_4   _____       _____      ____
job_3-job_5   _____       _____      ____
job_4-job_5   _____       _____      ____

Số cặp khớp: ____ / 6
```

So lại với bước 4. **Cùng một kết quả phân cụm, hai cách đo ra hai kết luận
trái ngược.** Cách nào đúng?

## Bước 6 — Thử ép chia 3 nhóm

Dữ liệu chỉ có 2 nghề. Giờ bắt máy chia thành 3.

Kết quả thật:

```
Mẫu A (k=3):   job_1 → 0   job_2 → 2   job_3 → 0   job_4 → 1   job_5 → 1
Mẫu B (k=3):   job_2 → 1   job_3 → 1   job_4 → 0   job_5 → 0   job_6 → 2
```

Lập lại bảng cặp:

```
            ở mẫu A     ở mẫu B     khớp?
job_2-job_3   _____       _____      ____
job_2-job_4   _____       _____      ____
job_2-job_5   _____       _____      ____
job_3-job_4   _____       _____      ____
job_3-job_5   _____       _____      ____
job_4-job_5   _____       _____      ____

Số cặp khớp: ____ / 6
```

## Bước 7 — So hai lựa chọn

```
k = 2:  ____ / 6 cặp khớp
k = 3:  ____ / 6 cặp khớp
```

**Chọn k nào? Vì sao?**

Gợi ý: cách chia nào biến mất khi dữ liệu đổi một chút?

---
---
---

# PHẦN B — ĐÁP ÁN

## Bước 1

```
Nhóm 1: job_1, job_2, job_3    — toàn PyTorch, OpenCV, YOLO
Nhóm 2: job_4, job_5, job_6    — toàn SQL, Power BI, Excel, Tableau
```

Hai nhóm không dùng chung skill nào.

## Bước 2

Trùng khớp hoàn toàn. Máy cũng ra đúng như vậy, ARI = **1.000**.

## Bước 3

```
Mẫu A — nhóm 1: job_1, job_2, job_3    nhóm 2: job_4, job_5
Mẫu B — nhóm 1: job_2, job_3           nhóm 2: job_4, job_5, job_6
```

## Bước 4

```
         A     B    trùng nhãn?
job_2    0     1       không
job_3    0     1       không
job_4    1     0       không
job_5    1     0       không

Số tin trùng nhãn: 0 / 4
```

So theo nhãn cho ra **0%** — nghĩa là "hai lần chạy chia hoàn toàn khác nhau".

**Sai hoàn toàn.** Hai lần chạy chia y hệt nhau, chỉ là máy gọi tên nhóm ngược
lại. Nhãn `0` và `1` chỉ là số thứ tự, phụ thuộc vào máy bắt đầu đoán từ đâu.

So theo nhãn là **cách so sai**.

## Bước 5

```
            ở mẫu A     ở mẫu B     khớp?
job_2-job_3   chung       chung      khớp
job_2-job_4   khác        khác       khớp
job_2-job_5   khác        khác       khớp
job_3-job_4   khác        khác       khớp
job_3-job_5   khác        khác       khớp
job_4-job_5   chung       chung      khớp

Số cặp khớp: 6 / 6
```

**100% khớp.** Đây mới là kết luận đúng.

Chỉ số làm đúng việc này tên là **ARI**. Ở đây ARI = **1.000**.

ARI đếm theo cặp chứ không theo nhãn, nên việc máy gọi nhóm là 0 hay 1 không
ảnh hưởng gì.

## Bước 6

```
            ở mẫu A     ở mẫu B     khớp?
job_2-job_3   khác        chung      LỆCH
job_2-job_4   khác        khác       khớp
job_2-job_5   khác        khác       khớp
job_3-job_4   khác        khác       khớp
job_3-job_5   khác        khác       khớp
job_4-job_5   chung       chung      khớp

Số cặp khớp: 5 / 6      ARI = 0.571
```

Cặp `job_2-job_3` lệch: mẫu A tách chúng ra, mẫu B để chung.

Hai tin này cùng là Computer Vision Engineer. Khi bị ép chia 3 nhóm, máy phải
cắt đôi nhóm CV — và cắt ở đâu thì tùy mẫu. Đó là một đường cắt **không có
thật trong dữ liệu**.

## Bước 7

```
k = 2:  6/6 cặp khớp    ARI = 1.000
k = 3:  5/6 cặp khớp    ARI = 0.571
```

**Chọn k = 2.**

Cách chia 2 nhóm sống sót khi dữ liệu đổi. Cách chia 3 nhóm thì không — đường
cắt thứ ba nhảy lung tung tùy mẫu, nghĩa là nó là đặc điểm của riêng mẫu đó,
không phải của thị trường.

Đó chính là **độ ổn định** (stability), và là lý do spec xếp nó trên các chỉ
số khác.

---
---
---

# PHẦN C — GIỜ MỞ `rq4.py`

| Bước làm tay | Chỗ trong `rq4.py` |
|---|---|
| 1. Gom nhóm chỉ nhìn skill | `run_clustering` — chỉ nhận `M`, không nhận title |
| 2. Mở tên nghề ra sau | `unblind`, `compare_to_titles` — gọi sau cùng |
| 3. Hai mẫu chồng lấn | `rng.choice(...)` hai lần trong `compute_stability` |
| 4. Nhãn tùy tiện | lý do tồn tại của cả hàm `compute_stability` |
| 5. So theo cặp | `adjusted_rand_score` |
| 6-7. Thử nhiều k rồi chọn | `run_clustering` quét k, `select_k` chọn |

## Thứ tự hàm chính là luật chống gian lận

```python
sweep  = run_clustering(M)        # title chưa xuất hiện
k      = select_k(sweep)          # chọn k, vẫn chưa thấy title
labels = _fit(M, k)               # chốt cụm
profiles = cluster_profiles(...)  # xem cụm gồm skill gì
unblinded = unblind(labels, ...)  # GIỜ mới ghép title vào
```

Đảo thứ tự hai dòng cuối lên trên là hỏng cả RQ4 — vì khi đã nhìn thấy title,
không ai chọn k một cách trung thực được nữa.

## Chỗ code khác cách làm tay

**Một — 100 lần, không phải 1.**

Anh bốc một cặp mẫu ở bước 3. Lần bốc khác có thể ra khác. Code bốc 100 cặp
mẫu rồi lấy ARI trung bình.

**Hai — quét k từ 2 đến 15, không phải 2 với 3.**

```python
for k in range(2, 16):
```

**Ba — hai chỉ số nữa ngoài stability.**

`silhouette` và `davies_bouldin` đo cụm có tách bạch gọn gàng không. Nhưng
**stability vẫn được xếp trên**, vì một cách chia có thể trông rất gọn mà vẫn
biến mất khi đổi mẫu — đúng như k=3 ở bước 6.

**Bốn — có cửa chặn.**

```python
check_minimum_size(n)   # dưới 300 tin thì từ chối chạy
```

Ví dụ này 6 tin, thật ra không đủ. Để 6 cho làm tay được.

---
---

# TỰ KIỂM TRA

Thêm tin thứ bảy, nằm giữa hai nhóm:

```
job_7:  Python, SQL
```

**Dự đoán:** với k=2, `job_7` rơi vào nhóm nào? Và độ ổn định tăng hay giảm?

Đáp án: `Python` thuộc nhóm CV, `SQL` thuộc nhóm DA — tin này không rõ thuộc
đâu. Mẫu khác nhau có thể đẩy nó sang hai phía khác nhau, nên các cặp chứa
`job_7` sẽ lúc khớp lúc lệch. Độ ổn định **giảm**.

Đây là chuyện sẽ xảy ra nhiều với dữ liệu thật: tin tuyển dụng lai giữa hai
nghề. Chúng kéo mọi chỉ số xuống, và đó là phản ánh đúng — ranh giới nghề
trong thực tế vốn không sắc nét.
