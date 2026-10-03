# RQ2 — LÀM TAY TRƯỚC, ĐỌC CODE SAU

Cầm giấy bút. Làm hết phần A rồi mới xem phần B.

Dữ liệu nhỏ đến mức nhẩm được, nhưng cách làm y hệt với 2.500 tin và 246 skill.

---
---

# PHẦN A — TÍNH TAY

## Dữ liệu

Sáu tin tuyển dụng:

```
job_1:  Python, SQL
job_2:  Python, SQL
job_3:  Python, PyTorch, OpenCV
job_4:  PyTorch, OpenCV
job_5:  Python, SQL
job_6:  PyTorch, OpenCV
```

## Bước 1 — Kẻ bảng 0/1

Mỗi dòng một tin, mỗi cột một skill. Ô = 1 nếu tin đó yêu cầu skill đó.

|  | OpenCV | PyTorch | Python | SQL |
|---|---|---|---|---|
| job_1 | | | | |
| job_2 | | | | |
| job_3 | | | | |
| job_4 | | | | |
| job_5 | | | | |
| job_6 | | | | |

## Bước 2 — Đếm theo cột

Cộng dọc từng cột. Mỗi skill có trong bao nhiêu tin?

```
OpenCV  = ____        Python = ____
PyTorch = ____        SQL    = ____
```

## Bước 3 — Đếm cặp

Với mỗi cặp, đếm số tin chứa **cả hai** skill.

```
OpenCV  + PyTorch = ____
OpenCV  + Python  = ____
OpenCV  + SQL     = ____
PyTorch + Python  = ____
PyTorch + SQL     = ____
Python  + SQL     = ____
```

## Bước 4 — Dừng lại, nhìn hai cặp này

```
OpenCV + PyTorch = ____
Python + SQL     = ____
```

Hai con số này bằng nhau.

**Câu hỏi:** vậy hai cặp này liên quan với nhau mạnh như nhau, đúng không?

Viết câu trả lời ra giấy trước khi đọc tiếp.

## Bước 5 — Đổi sang xác suất

Tổng cộng **n = 6** tin.

Xác suất một tin bất kỳ yêu cầu skill đó:

```
P(OpenCV)  = 3/6 = ____
P(PyTorch) = ___ = ____
P(Python)  = ___ = ____
P(SQL)     = ___ = ____
```

## Bước 6 — Nếu KHÔNG liên quan thì sẽ gặp nhau bao nhiêu?

Đây là ý quan trọng nhất của cả RQ2.

Giả sử hai skill hoàn toàn độc lập — việc một tin có OpenCV không ảnh hưởng
gì tới việc nó có PyTorch hay không. Khi đó xác suất gặp cả hai là:

```
P(a) × P(b)
```

Tính cho hai cặp:

```
OpenCV + PyTorch:   P(a) × P(b) = ____ × ____ = ____
Python + SQL:       P(a) × P(b) = ____ × ____ = ____
```

## Bước 7 — Thực tế gặp nhau bao nhiêu?

Lấy số đếm ở bước 3 chia cho 6:

```
OpenCV + PyTorch:   P(a,b) = ___/6 = ____
Python + SQL:       P(a,b) = ___/6 = ____
```

## Bước 8 — Chia hai số cho nhau

```
            thực tế        P(a,b)
   lift = ------------ = -----------
           ngẫu nhiên    P(a) × P(b)
```

```
OpenCV + PyTorch:   lift = ____ / ____ = ____
Python + SQL:       lift = ____ / ____ = ____
```

## Bước 9 — Kết luận

Hai cặp có cùng số đếm ở bước 3. Nhưng lift khác nhau.

Giải thích bằng lời: **vì sao?**

Gợi ý: nhìn lại bước 2, xem Python xuất hiện ở bao nhiêu tin.

---
---
---

# PHẦN B — ĐÁP ÁN

Chỉ xem sau khi đã làm xong phần A.

## Bước 1

|  | OpenCV | PyTorch | Python | SQL |
|---|---|---|---|---|
| job_1 | 0 | 0 | 1 | 1 |
| job_2 | 0 | 0 | 1 | 1 |
| job_3 | 1 | 1 | 1 | 0 |
| job_4 | 1 | 1 | 0 | 0 |
| job_5 | 0 | 0 | 1 | 1 |
| job_6 | 1 | 1 | 0 | 0 |

## Bước 2

```
OpenCV  = 3        Python = 4
PyTorch = 3        SQL    = 3
```

## Bước 3

```
OpenCV  + PyTorch = 3
OpenCV  + Python  = 1
OpenCV  + SQL     = 0
PyTorch + Python  = 1
PyTorch + SQL     = 0
Python  + SQL     = 3
```

## Bước 4

Cả hai đều bằng **3**.

Nếu câu trả lời của anh là "ừ, mạnh như nhau" thì anh vừa rơi đúng vào cái bẫy
mà task mục 3.1 cảnh báo:

> Không được chỉ kết luận: Python và SQL thường đi cùng nhau.

## Bước 5

```
P(OpenCV)  = 3/6 = 0.50
P(PyTorch) = 3/6 = 0.50
P(Python)  = 4/6 = 0.67
P(SQL)     = 3/6 = 0.50
```

## Bước 6

```
OpenCV + PyTorch:   0.50 × 0.50 = 0.25
Python + SQL:       0.67 × 0.50 = 0.33
```

## Bước 7

```
OpenCV + PyTorch:   3/6 = 0.50
Python + SQL:       3/6 = 0.50
```

Thực tế giống hệt nhau.

## Bước 8

```
OpenCV + PyTorch:   0.50 / 0.25 = 2.00
Python + SQL:       0.50 / 0.33 = 1.50
```

## Bước 9 — vì sao khác nhau

**Python có mặt ở 4 trên 6 tin.** Nó ở khắp nơi.

Một skill phổ biến như thế thì đụng SQL 3 lần là **chuyện đương nhiên** — không
cần có liên hệ gì giữa chúng.

OpenCV và PyTorch mỗi cái chỉ 3/6, ít phổ biến hơn, **vậy mà vẫn dính nhau đủ
3 lần**. Lần nào có OpenCV là có PyTorch. Đó mới là liên hệ thật.

lift chia đúng cho mức phổ biến, nên nó tách được hai trường hợp. Đếm thô thì
không.

---
---
---

# PHẦN C — GIỜ MỞ `rq2.py`

Từng bước ở trên ứng với đúng một chỗ trong code.

| Bước làm tay | Dòng trong `rq2.py` |
|---|---|
| 1. Kẻ bảng 0/1 | không nằm ở đây — `synthetic.build_matrix()` làm |
| 2. Đếm theo cột | `M.sum()` trong `compute_skill_frequency` |
| 3. Đếm cặp | `C = M.T.values @ M.values` trong `compute_cooccurrence` |
| 5. Đổi sang xác suất | `pa = ... / n` và `pb = ... / n` |
| 6. Mức ngẫu nhiên | `pa * pb` |
| 7. Mức thực tế | `pab = pairs["joint"] / n` |
| 8. Chia | `out["lift"] = pab / (pa * pb)` |

## Chỗ duy nhất code khác cách làm tay

Bước 3. Anh đếm từng cặp một, sáu lần. Code đếm **tất cả cùng lúc**:

```python
C = M.T.values @ M.values
```

Nhân ma trận chuyển vị với chính nó. Kết quả:

```
         OpenCV  PyTorch  Python  SQL
OpenCV        3        3       1    0
PyTorch       3        3       1    0
Python        1        1       4    3
SQL           0        0       3    3
```

So lại với bước 3 — y hệt. Đường chéo chính là bước 2.

Với 4 skill thì đếm tay được. Với 246 skill là 30.135 cặp, nhân với 2.500 tin.
Phép nhân ma trận làm xong trong tích tắc.

## Hai chỉ số còn lại

`npmi` và `jaccard` cùng ý tưởng với lift, chỉ khác cách chuẩn hóa:

- **lift** dễ hiểu nhất, nhưng cặp hiếm cho ra số rất to
- **npmi** ép về khoảng −1 đến 1, nên cặp phổ biến và cặp hiếm so sánh được
- **jaccard** dè dặt nhất, thiên về cặp phổ biến

Báo cáo cả ba vì mỗi cái sai theo một kiểu. Cặp nào mạnh ở cả ba thì chắc chắn.

---
---

# TỰ KIỂM TRA

Thêm vào dữ liệu một tin thứ bảy:

```
job_7:  Python
```

Tính lại bước 2, 5, 6, 8 cho cặp `Python + SQL`.

**Dự đoán trước khi tính:** lift của cặp này tăng hay giảm?

Đáp án: n = 7, Python = 5, SQL = 3, joint vẫn 3.
P(Python) = 0.71, P(SQL) = 0.43, tích = 0.31.
P(a,b) = 3/7 = 0.43. lift = 0.43 / 0.31 = **1.40**.

Giảm, từ 1.50 xuống 1.40. Python phổ biến hơn nữa, nên việc nó gặp SQL càng
kém ý nghĩa.

Hiểu được chỗ này là nắm xong RQ2.
