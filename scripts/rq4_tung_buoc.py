"""Chạy từng bước của RQ4 trên 6 tin, in ra để nhìn.

    python scripts/rq4_tung_buoc.py

Đi theo docs/analysis/rq4_lam_tay.md. Dữ liệu nhỏ, nhẩm tay kiểm được.
"""
import itertools
import sys
from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

JOBS = {
    "job_1": ("Computer Vision Engineer", ["Python", "PyTorch", "OpenCV"]),
    "job_2": ("Computer Vision Engineer", ["Python", "PyTorch", "YOLO"]),
    "job_3": ("Computer Vision Engineer", ["PyTorch", "OpenCV", "YOLO"]),
    "job_4": ("Data Analyst", ["SQL", "Power BI", "Excel"]),
    "job_5": ("Data Analyst", ["SQL", "Power BI", "Tableau"]),
    "job_6": ("Data Analyst", ["SQL", "Excel", "Tableau"]),
}

SKILLS = sorted({s for _, sk in JOBS.values() for s in sk})
M = pd.DataFrame(
    [[1 if s in sk else 0 for s in SKILLS] for _, sk in JOBS.values()],
    index=list(JOBS), columns=SKILLS,
)


def muc(tieu_de):
    print(f"\n{'=' * 68}\n{tieu_de}\n{'=' * 68}")


def gom_nhom(ten_tin, k, seed):
    """Chạy K-Means trên một nhóm tin, trả về {tên tin: số nhóm}."""
    nhan = KMeans(n_clusters=k, n_init=1, random_state=seed).fit_predict(
        M.loc[ten_tin].values.astype(float)
    )
    return dict(zip(ten_tin, nhan))


def bang_cap(giao, A, B):
    """In bảng so theo cặp, trả về số cặp khớp."""
    print(f"   {'cặp':<16}{'ở mẫu A':<10}{'ở mẫu B':<10}")
    khop = 0
    cap = list(itertools.combinations(giao, 2))
    for a, b in cap:
        ca = "chung" if A[a] == A[b] else "khác"
        cb = "chung" if B[a] == B[b] else "khác"
        ok = ca == cb
        khop += ok
        print(f"   {a + '-' + b:<16}{ca:<10}{cb:<10}{'khớp' if ok else '>>> LỆCH'}")
    return khop, len(cap)


# ---------------------------------------------------------------------
muc("DỮ LIỆU — 6 tin, tên nghề đang bị che")

for ten, (_, sk) in JOBS.items():
    print(f"   {ten}:  {', '.join(sk)}")

print("\nDạng bảng 0/1 mà máy đọc:")
print(M.to_string())


# ---------------------------------------------------------------------
muc("BƯỚC 1 — gom 2 nhóm, chỉ nhìn skill")

nhan = gom_nhom(list(JOBS), k=2, seed=42)
for nhom in sorted(set(nhan.values())):
    thanh_vien = [t for t in JOBS if nhan[t] == nhom]
    print(f"   nhóm {nhom}: {', '.join(thanh_vien)}")

print("\n   Hai nhóm không dùng chung skill nào.")


# ---------------------------------------------------------------------
muc("BƯỚC 2 — GIỜ mới mở tên nghề ra")

for ten, (title, _) in JOBS.items():
    print(f"   {ten}  ->  nhóm {nhan[ten]}   {title}")

nghe_that = [t for t, _ in JOBS.values()]
print(f"\n   ARI (khớp với nghề thật) = "
      f"{adjusted_rand_score(nghe_that, list(nhan.values())):.3f}")
print("   1.000 = trùng khớp hoàn toàn.")
print("\n   Thứ tự quan trọng: gom TRƯỚC, mở tên SAU.")
print("   Biết tên trước rồi mới gom thì chỉ là chép lại cái tên.")


# ---------------------------------------------------------------------
muc("BƯỚC 3 — bỏ bớt mỗi mẫu một tin, gom lại")

MAU_A = ["job_1", "job_2", "job_3", "job_4", "job_5"]      # bỏ job_6
MAU_B = ["job_2", "job_3", "job_4", "job_5", "job_6"]      # bỏ job_1

A = gom_nhom(MAU_A, k=2, seed=0)
B = gom_nhom(MAU_B, k=2, seed=0)

print("   Mẫu A:", "   ".join(f"{t}->{n}" for t, n in A.items()))
print("   Mẫu B:", "   ".join(f"{t}->{n}" for t, n in B.items()))

GIAO = [t for t in MAU_A if t in MAU_B]
print(f"\n   Có mặt ở cả hai mẫu: {', '.join(GIAO)}")


# ---------------------------------------------------------------------
muc("BƯỚC 4 — so theo NHÃN (cách sai)")

print(f"   {'tin':<10}{'A':<5}{'B':<5}trùng nhãn?")
trung = 0
for t in GIAO:
    ok = A[t] == B[t]
    trung += ok
    print(f"   {t:<10}{A[t]:<5}{B[t]:<5}{'có' if ok else 'không'}")

print(f"\n   Trùng nhãn: {trung}/{len(GIAO)}")
print("\n   Kết luận theo cách này: 'hai lần chạy chia hoàn toàn khác nhau'.")
print("   SAI. Nhìn lại bước 3 — hai lần chia y hệt nhau, máy chỉ gọi")
print("   ngược tên nhóm. Số 0 và 1 là số thứ tự tùy tiện.")


# ---------------------------------------------------------------------
muc("BƯỚC 5 — so theo CẶP (cách đúng)")

print("   Không hỏi 'tin này nhãn mấy'.")
print("   Hỏi: 'hai tin này có bị xếp CHUNG nhóm không?'\n")

khop, tong = bang_cap(GIAO, A, B)
ari = adjusted_rand_score([A[t] for t in GIAO], [B[t] for t in GIAO])
print(f"\n   Khớp: {khop}/{tong} cặp      ARI = {ari:.3f}")
print("\n   Cùng một kết quả phân cụm. Bước 4 ra 0%, bước 5 ra 100%.")
print("   ARI đếm theo cặp nên không quan tâm nhóm tên là gì.")


# ---------------------------------------------------------------------
muc("BƯỚC 6 — ép chia 3 nhóm, dù dữ liệu chỉ có 2 nghề")

A3 = gom_nhom(MAU_A, k=3, seed=0)
B3 = gom_nhom(MAU_B, k=3, seed=3)
print("   Mẫu A:", "   ".join(f"{t}->{n}" for t, n in A3.items()))
print("   Mẫu B:", "   ".join(f"{t}->{n}" for t, n in B3.items()))
print()

khop3, tong3 = bang_cap(GIAO, A3, B3)
ari3 = adjusted_rand_score([A3[t] for t in GIAO], [B3[t] for t in GIAO])
print(f"\n   Khớp: {khop3}/{tong3} cặp      ARI = {ari3:.3f}")
print("\n   job_2 và job_3 cùng là Computer Vision Engineer.")
print("   Bị ép chia 3, máy phải cắt đôi nhóm đó — và cắt ở đâu thì tùy mẫu.")
print("   Đường cắt thứ ba không có thật trong dữ liệu.")


# ---------------------------------------------------------------------
muc("BƯỚC 7 — chọn k")

print(f"   k = 2:  {khop}/{tong} cặp khớp    ARI = {ari:.3f}")
print(f"   k = 3:  {khop3}/{tong3} cặp khớp    ARI = {ari3:.3f}")
print("\n   Chọn k = 2.")
print("   Cách chia 2 nhóm sống sót khi dữ liệu đổi. Cách chia 3 thì không.")
print("   Cái gì biến mất khi đổi mẫu thì là đặc điểm của mẫu,")
print("   không phải của thị trường.")
print("\n   Đó là 'độ ổn định', và là lý do spec xếp nó trên các chỉ số khác.")
