# RQ3 — LÀM TAY TRƯỚC, ĐỌC CODE SAU

Cầm giấy bút. Làm hết phần A rồi mới xem phần B.

RQ3 hỏi: **tên công việc có nói đúng công việc không?** Hai chiều, làm riêng.

---
---

# PHẦN A — TÍNH TAY

## Dữ liệu

Chín tin, ba title:

```
ML Engineer
  job_1:  Python, PyTorch, OpenCV
  job_2:  Python, LLM, RAG
  job_3:  Python, PyTorch, LLM

Data Analyst
  job_4:  SQL, Power BI, Excel
  job_5:  SQL, Power BI, Excel
  job_6:  SQL, Power BI, Tableau

BI Analyst
  job_7:  SQL, Power BI, Excel
  job_8:  SQL, Power BI, Tableau
  job_9:  SQL, Excel, Tableau
```

---

# CHIỀU 1 — CÙNG TITLE, SKILL CÓ GIỐNG NHAU KHÔNG?

## Bước 1 — Đo độ giống nhau của hai tin

Công cụ: **Jaccard**. Hai tin giống nhau bao nhiêu phần trăm.

```
                 số skill CẢ HAI cùng có
   jaccard = ---------------------------------
              số skill có ở ÍT NHẤT MỘT trong hai
```

Làm thử `job_1` và `job_2`:

```
job_1:  Python, PyTorch, OpenCV
job_2:  Python, LLM, RAG

cả hai cùng có     : ____            (gạch ra giấy)
ít nhất một bên có : ____
jaccard            = ____ / ____ = ____
```

## Bước 2 — Làm hết các cặp trong ML Engineer

Ba tin thì có ba cặp.

```
job_1 - job_2 :  chung ___  tổng ___  →  ____
job_1 - job_3 :  chung ___  tổng ___  →  ____
job_2 - job_3 :  chung ___  tổng ___  →  ____

jaccard trung bình = ____
```

## Bước 3 — Đổi sang "độ phân tán"

Jaccard cao = các tin giống nhau. Nhưng ta muốn đo **độ khác nhau**, nên lấy
1 trừ đi:

```
   phân tán = 1 − jaccard trung bình
```

```
ML Engineer:  phân tán = 1 − ____ = ____
```

## Bước 4 — Làm nốt hai title kia

```
Data Analyst:   jaccard TB = ____    phân tán = ____
BI Analyst:     jaccard TB = ____    phân tán = ____
```

Xếp hạng ba title theo độ phân tán, cao xuống thấp:

```
1. ________  ____
2. ________  ____
3. ________  ____
```

## Bước 5 — Dừng lại. Câu hỏi quan trọng nhất của RQ3

ML Engineer có phân tán cao nhất.

**Vậy nó CAO hay THẤP?**

Đừng trả lời vội. Nghĩ xem: cao so với cái gì?

Viết ra giấy: muốn biết 0.6 là cao hay thấp thì cần biết thêm thông tin gì?

## Bước 6 — Mốc so sánh

Bốc đại 3 tin bất kỳ, **không cần cùng title**, rồi đo phân tán của nhóm đó.

Lấy `job_1`, `job_4`, `job_6`:

```
job_1 - job_4 :  chung ___  tổng ___  →  ____
job_1 - job_6 :  chung ___  tổng ___  →  ____
job_4 - job_6 :  chung ___  tổng ___  →  ____

jaccard TB = ____      phân tán = ____
```

## Bước 7 — So lại

```
nhóm bốc đại    : ____
ML Engineer     : ____
Data Analyst    : ____
BI Analyst      : ____
```

**Ba title có phân tán thấp hơn nhóm bốc đại không?**

Nếu CÓ → title đó có ý nghĩa, nó gom được các tin giống nhau.
Nếu KHÔNG → title đó vô dụng, không hơn gì một cái nhãn dán bừa.

Đây chính là `bootstrap_baseline`. Code bốc 1.000 nhóm ngẫu nhiên thay vì 1,
nhưng ý tưởng y hệt.

---

# CHIỀU 2 — TITLE KHÁC NHAU, SKILL CÓ GIỐNG NHAU KHÔNG?

## Bước 8 — Lập hồ sơ cho mỗi title

Hồ sơ = **tỉ lệ tin trong title đó có skill này**.

Làm cho `Data Analyst` (job_4, job_5, job_6):

```
SQL       : có ở ___/3 tin  =  ____
Power BI  : có ở ___/3 tin  =  ____
Excel     : có ở ___/3 tin  =  ____
Tableau   : có ở ___/3 tin  =  ____
Python    : có ở ___/3 tin  =  ____
```

Làm tiếp cho `BI Analyst` (job_7, job_8, job_9):

```
SQL       : ____
Power BI  : ____
Excel     : ____
Tableau   : ____
Python    : ____
```

## Bước 9 — Nhìn hai hồ sơ cạnh nhau

```
             Data Analyst    BI Analyst
SQL              ____           ____
Power BI         ____           ____
Excel            ____           ____
Tableau          ____           ____
Python           ____           ____
```

**Hai title này đang tả cùng một công việc, hay hai công việc khác nhau?**

Trả lời bằng lời, chưa cần tính gì.

## Bước 10 — Và so với ML Engineer?

Hồ sơ `ML Engineer` có `SQL` không? Có `Power BI` không?

Việc so hồ sơ bằng số gọi là **cosine**. Phần số học hơi nặng nên để code làm,
nhưng ý nghĩa thì nhìn bảng ở bước 9 là thấy ngay.

---
---
---

# PHẦN B — ĐÁP ÁN

## Bước 1

```
job_1:  Python, PyTorch, OpenCV
job_2:  Python, LLM, RAG

cả hai cùng có     : Python                                → 1
ít nhất một bên có : Python, PyTorch, OpenCV, LLM, RAG     → 5
jaccard = 1/5 = 0.200
```

## Bước 2 — ML Engineer

```
job_1 - job_2 :  chung 1  tổng 5  →  0.200
job_1 - job_3 :  chung 2  tổng 4  →  0.500
job_2 - job_3 :  chung 2  tổng 4  →  0.500

jaccard trung bình = (0.200 + 0.500 + 0.500) / 3 = 0.400
```

## Bước 3

```
ML Engineer:  phân tán = 1 − 0.400 = 0.600
```

## Bước 4

```
Data Analyst
  job_4 - job_5 :  chung 3  tổng 3  →  1.000     (hai tin giống hệt nhau)
  job_4 - job_6 :  chung 2  tổng 4  →  0.500
  job_5 - job_6 :  chung 2  tổng 4  →  0.500
  jaccard TB = 0.667    phân tán = 0.333

BI Analyst
  cả ba cặp đều chung 2 tổng 4  →  0.500
  jaccard TB = 0.500    phân tán = 0.500
```

Xếp hạng:

```
1. ML Engineer    0.600
2. BI Analyst     0.500
3. Data Analyst   0.333
```

## Bước 5

Câu trả lời đúng: **chưa biết được.**

0.6 không cao cũng không thấp cho tới khi biết một nhóm *bất kỳ* thì được bao
nhiêu. Thiếu mốc so sánh thì con số này vô nghĩa.

Nếu lúc nãy anh trả lời "cao" thì đó đúng là lỗi mà `bootstrap_baseline` sinh
ra để chặn.

## Bước 6

```
job_1 - job_4 :  chung 0  tổng 6  →  0.000
job_1 - job_6 :  chung 0  tổng 6  →  0.000
job_4 - job_6 :  chung 2  tổng 4  →  0.500

jaccard TB = 0.167      phân tán = 0.833
```

## Bước 7

```
nhóm bốc đại    : 0.833
ML Engineer     : 0.600     thấp hơn  →  có ý nghĩa
BI Analyst      : 0.500     thấp hơn  →  có ý nghĩa
Data Analyst    : 0.333     thấp hơn  →  có ý nghĩa
```

Cả ba title đều gom được các tin giống nhau hơn mức ngẫu nhiên.

ML Engineer là title **yếu nhất** trong ba cái — 0.600 đã khá gần 0.833. Nhìn
lại dữ liệu thì rõ: có tin đòi `PyTorch, OpenCV` (thị giác máy tính), có tin
đòi `LLM, RAG` (mô hình ngôn ngữ). Cùng một cái tên, hai loại việc.

Đó chính là phát hiện mà RQ3 đi tìm.

## Bước 8–9

```
             Data Analyst    BI Analyst
SQL              1.00           1.00
Power BI         1.00           0.67
Excel            0.67           0.67
Tableau          0.33           0.67
Python           0.00           0.00
```

Gần như trùng khớp. **Hai cái tên, một công việc.**

Code tính cosine ra **0.956** — gần 1 hết mức.

## Bước 10

```
             Data Analyst    ML Engineer
SQL              1.00           0.00
Power BI         1.00           0.00
Python           0.00           1.00
PyTorch          0.00           0.67
```

Không chồng lấn chút nào. cosine = **0.000**.

Bảng đầy đủ:

```
                BI Analyst   Data Analyst   ML Engineer
BI Analyst          1.000         0.956          0.000
Data Analyst        0.956         1.000          0.000
ML Engineer         0.000         0.000          1.000
```

---
---
---

# PHẦN C — GIỜ MỞ `rq3.py`

| Bước làm tay | Hàm trong `rq3.py` |
|---|---|
| 1–2. Jaccard từng cặp | `_mean_pairwise_jaccard` |
| 3–4. 1 trừ trung bình | `compute_title_dispersion` |
| 6. Nhóm bốc đại | `bootstrap_baseline` |
| 7. So với mốc | `add_baselines`, cột `informative` |
| 8. Lập hồ sơ title | `M.groupby(titles).mean()` |
| 9–10. So hồ sơ | `compute_title_similarity` |

## Chỗ code khác cách làm tay

**Một — bốc 1.000 lần, không phải 1.**

Anh bốc một nhóm ở bước 6, được 0.833. Bốc nhóm khác có thể ra 0.7 hoặc 0.9.
Một lần bốc thì hên xui. Code bốc 1.000 lần rồi lấy khoảng:

```python
"mean": trung bình của 1000 lần
"p5":   mức thấp nhất của 5% lần thấp nhất
```

Title chỉ được tính là có ý nghĩa khi phân tán của nó **thấp hơn cả p5** —
tức thấp hơn gần như mọi nhóm ngẫu nhiên.

**Hai — nhóm ngẫu nhiên phải cùng cỡ.**

Title có 3 tin thì nhóm ngẫu nhiên cũng phải 3 tin. Nhóm nhỏ luôn nhiễu hơn
nhóm to, nên so với nhóm khác cỡ là tự tạo ra kết quả giả.

**Ba — tính Jaccard tất cả cùng lúc.**

Anh làm 3 cặp bằng tay. Với một title có 50 tin là 1.225 cặp. Code dùng phép
nhân ma trận, giống `M.T @ M` ở RQ2:

```python
inter = X @ X.T                    # số skill chung, mọi cặp
sizes = X.sum(axis=1)
union = sizes[:,None] + sizes[None,:] - inter
```

**Bốn — title dưới 5 tin bị bỏ qua.**

Ví dụ này mỗi title có 3 tin, thật ra chưa đủ ngưỡng. Code sẽ xếp cả ba vào
`skipped_titles` chứ không tính. Ở đây để 3 cho dễ làm tay.

Lý do ngưỡng 5: 3 tin chỉ cho 3 cặp, trung bình trên 3 cặp quá nhiễu. 5 tin
cho 10 cặp.

---
---

# TỰ KIỂM TRA

Thêm `job_10` vào `ML Engineer`:

```
job_10:  Python, PyTorch, OpenCV      (giống hệt job_1)
```

**Dự đoán trước khi tính:** phân tán của ML Engineer tăng hay giảm?

Đáp án: giờ có 4 tin, 6 cặp. Cặp mới `job_1 - job_10` giống hệt nhau → jaccard
1.000. Hai cặp còn lại `job_10` với job_2, job_3 giống hệt cặp của job_1.

```
0.200 + 0.500 + 0.500 + 1.000 + 0.200 + 0.500 = 2.900
jaccard TB = 2.900 / 6 = 0.483
phân tán = 1 − 0.483 = 0.517
```

Giảm, từ 0.600 xuống 0.517. Thêm một tin trùng làm title trông nhất quán hơn.

**Đây là một vấn đề thật:** tin trùng lặp kéo phân tán xuống một cách giả tạo.
Vì thế bước làm sạch phải loại trùng trước khi RQ3 chạy — và đó là việc của
Đức, không phải của mình.
