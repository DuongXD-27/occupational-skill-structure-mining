"""Vẽ hình cho RQ4.

Mục 6 của task đòi "PCA visualization". Spec mục 5 nói rõ hơn: hai biểu đồ PCA
đặt CẠNH NHAU, một tô màu theo cụm, một theo title.

Lý do phải đặt cạnh nhau: con số ARI khó cảm nhận. Hai bức tranh lệch nhau thì
nhìn phát hiểu ngay — và chênh lệch giữa hai bức CHÍNH LÀ câu trả lời của RQ4.
"""

import matplotlib
matplotlib.use("Agg")                      # không mở cửa sổ, chỉ ghi file

import matplotlib.pyplot as plt
import pandas as pd

# Bảng màu đã qua kiểm định cho biểu đồ phân tán (4 màu, mọi cặp đều phân biệt
# được kể cả với người mù màu). Gán theo thứ tự cố định, không xoay vòng.
MAU = ["#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"]
HINH = ["o", "s", "^", "D"]                # dạng điểm — để nhận ra không chỉ bằng màu

MUC_XAM = "#52514e"
MUC_NHAT = "#8a8a86"


def _dinh_dang_truc(ax):
    """Trục và lưới phải lùi về sau, không tranh với dữ liệu."""
    ax.grid(True, color="#e8e8e4", linewidth=0.6)
    ax.set_axisbelow(True)

    for canh in ("top", "right"):
        ax.spines[canh].set_visible(False)
    for canh in ("left", "bottom"):
        ax.spines[canh].set_color("#d8d8d4")

    ax.tick_params(colors=MUC_NHAT, labelsize=8)


def _luu(fig, duong_dan):
    """Ghi hình ra file rồi đóng lại."""
    duong_dan = str(duong_dan)
    fig.savefig(duong_dan, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    return duong_dan


def _ve_mot_khung(ax, pca, nhan, tieu_de, chu_thich_toi_da=8, sap_xep=False):
    """Vẽ một khung phân tán, tô màu theo `nhan`.

    sap_xep=True  : xếp chú thích theo tên (dùng cho cụm: 0, 1, 2, 3)
    sap_xep=False : xếp theo số tin, nhiều nhất trước (dùng cho title)
    """
    gia_tri = pd.Series(nhan).values
    nhom = pd.Series(nhan).value_counts().index[:chu_thich_toi_da]
    if sap_xep:
        nhom = sorted(nhom)

    for i, ten in enumerate(nhom):
        diem = pca[gia_tri == ten]
        ax.scatter(
            diem["x"], diem["y"],
            s=34,
            c=MAU[i % len(MAU)],
            marker=HINH[(i // len(MAU)) % len(HINH)],
            edgecolors="white", linewidths=0.7,     # viền trắng khi điểm chồng nhau
            label=str(ten),
        )

    ax.set_title(tieu_de, fontsize=11, color="#0b0b0b", pad=10)
    ax.set_xlabel("PC1", fontsize=9, color=MUC_XAM)
    ax.set_ylabel("PC2", fontsize=9, color=MUC_XAM)

    _dinh_dang_truc(ax)

    ax.legend(
        fontsize=8, frameon=False, labelcolor=MUC_XAM,
        loc="upper center", bbox_to_anchor=(0.5, -0.13),
        ncol=2, handletextpad=0.3, columnspacing=1.0,
    )


def ve_pca(result, titles, duong_dan="reports/analysis/rq4_pca.png"):
    """Hai khung PCA cạnh nhau: trái tô theo cụm, phải tô theo title.

    Hai bức giống nhau  -> tên nghề phản ánh đúng công việc.
    Hai bức khác nhau   -> tên nghề và công việc thật đã lệch nhau.
    """
    pca = result["pca"]
    ari = result.get("agreement", {}).get("ari")

    fig, (trai, phai) = plt.subplots(1, 2, figsize=(11, 5.4), sharex=True, sharey=True)
    fig.patch.set_facecolor("#fcfcfb")

    _ve_mot_khung(trai, pca, pca["cluster"].map(lambda c: f"Cụm {c}"),
                  "Thuật toán tự gom — chưa nhìn thấy title", sap_xep=True)
    _ve_mot_khung(phai, pca, titles.reindex(pca["job_id"]),
                  "Tô theo title do nhà tuyển dụng đặt")

    phu_de = "RQ4 — cấu trúc thuật toán tìm ra, so với tên nghề đang dùng"
    if ari is not None:
        phu_de += f"      ARI = {ari:.3f}"
    fig.suptitle(phu_de, fontsize=12, color="#0b0b0b", y=0.99)

    fig.tight_layout(rect=[0, 0, 1, 0.96])

    return _luu(fig, duong_dan)


def ve_quet_k(sweep, chosen_k, duong_dan="reports/analysis/rq4_sweep_k.png"):
    """Ba chỉ số theo từng k, và k được chọn.

    Mỗi chỉ số một khung riêng — không bao giờ nhét hai thang đo khác nhau lên
    cùng một trục.
    """
    chi_so = [
        ("stability", "Độ ổn định — cao là tốt"),
        ("silhouette", "Silhouette — cao là tốt"),
        ("davies_bouldin", "Davies-Bouldin — thấp là tốt"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
    fig.patch.set_facecolor("#fcfcfb")

    for ax, (cot, nhan) in zip(axes, chi_so):
        ax.plot(sweep["k"], sweep[cot], color=MAU[0], linewidth=2,
                marker="o", markersize=5,
                markeredgecolor="white", markeredgewidth=0.7)

        ax.axvline(chosen_k, color=MUC_NHAT, linewidth=1, linestyle="--")
        ax.annotate(f"k = {chosen_k}", xy=(chosen_k, ax.get_ylim()[1]),
                    xytext=(4, -10), textcoords="offset points",
                    fontsize=8, color=MUC_XAM)

        ax.set_title(nhan, fontsize=10, color="#0b0b0b")
        ax.set_xlabel("số cụm (k)", fontsize=9, color=MUC_XAM)
        _dinh_dang_truc(ax)

    fig.tight_layout()

    return _luu(fig, duong_dan)
