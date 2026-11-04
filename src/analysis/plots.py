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


# ---------------------------------------------------------------------------
# Thang màu liên tục. Tuần tự: một sắc xanh, nhạt -> đậm (độ lớn).
# Phân kỳ: xanh <-> đỏ, giữa là xám trung tính (dấu âm/dương, ví dụ NPMI).
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

TUAN_TU = LinearSegmentedColormap.from_list(
    "xanh", ["#f4f8fd", "#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#104281", "#0d366b"])
PHAN_KY = LinearSegmentedColormap.from_list(
    "xanh_do", ["#104281", "#3987e5", "#f0efec", "#e66767", "#a8302f"])
from .config import MIN_COOCCURRENCE as MIN_COOC  # noqa: E402

MAU_KHAC = "#b5b4af"            # nhóm gộp "khác" — xám, không phải màu thứ 5


def _nhan_ngan(s, toi_da=28):
    s = str(s)
    return s if len(s) <= toi_da else s[: toi_da - 1] + "…"


# ------------------------------------------------------------------ RQ2

def ve_top_skill(freq, duong_dan, top=30):
    """Thanh ngang: top `top` skill theo tỉ lệ tin yêu cầu. Một chuỗi -> một màu."""
    d = freq.head(top).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7.5, 0.24 * len(d) + 1.2))
    fig.patch.set_facecolor("#fcfcfb")
    ax.barh(d["skill"], d["share"] * 100, color=MAU[0], height=0.7)
    for y, (v, n) in enumerate(zip(d["share"], d["n_postings"])):
        ax.text(v * 100 + 0.5, y, f"{v * 100:.0f}%  ({n})", va="center", fontsize=7, color=MUC_XAM)
    ax.set_xlabel("% tin tuyển dụng hợp lệ có yêu cầu skill", fontsize=9, color=MUC_XAM)
    ax.set_title(f"RQ2 — {len(d)} kỹ năng được yêu cầu nhiều nhất", fontsize=11, color="#0b0b0b")
    _dinh_dang_truc(ax)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", labelsize=8, colors=MUC_XAM)
    ax.set_xlim(0, min(100, d["share"].max() * 100 * 1.25 + 5))
    fig.tight_layout()
    return _luu(fig, duong_dan)


def ve_heatmap_lien_ket(M, assoc, duong_dan, top=20):
    """NPMI giữa `top` skill phổ biến nhất. Ô trống = cặp chưa đạt ngưỡng đồng xuất hiện."""
    import numpy as np
    ten = list(M.sum().sort_values(ascending=False).head(top).index)
    vi_tri = {s: i for i, s in enumerate(ten)}
    lu = np.full((len(ten), len(ten)), np.nan)
    for a, b, v in assoc[["skill_a", "skill_b", "npmi"]].itertuples(index=False):
        if a in vi_tri and b in vi_tri:
            lu[vi_tri[a], vi_tri[b]] = lu[vi_tri[b], vi_tri[a]] = v
    fig, ax = plt.subplots(figsize=(8, 7))
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    # ô chưa đạt ngưỡng: gạch chéo, để không lẫn với NPMI ≈ 0 (xám nhạt)
    from matplotlib.patches import Rectangle
    ax.add_patch(Rectangle((-0.5, -0.5), len(ten), len(ten), facecolor="#fcfcfb",
                           hatch="////", edgecolor="#dedcd6", linewidth=0, zorder=0))
    anh = ax.imshow(np.ma.masked_invalid(lu), cmap=PHAN_KY, vmin=-1, vmax=1, zorder=1)
    ax.set_xticks(range(len(ten)), [_nhan_ngan(s, 18) for s in ten], rotation=60, ha="right", fontsize=7)
    ax.set_yticks(range(len(ten)), [_nhan_ngan(s, 18) for s in ten], fontsize=7)
    ax.tick_params(colors=MUC_XAM, length=0)
    for canh in ax.spines.values():
        canh.set_visible(False)
    thanh = fig.colorbar(anh, ax=ax, shrink=0.7)
    thanh.set_label("NPMI  (−1 tránh nhau · 0 độc lập · 1 luôn đi cùng)", fontsize=8, color=MUC_XAM)
    thanh.ax.tick_params(labelsize=7, colors=MUC_NHAT)
    ax.set_title(f"RQ2 — liên kết giữa {len(ten)} skill phổ biến nhất (ô gạch: < "
                 f"{MIN_COOC} lần đi cùng)",
                 fontsize=10, color="#0b0b0b")
    fig.tight_layout()
    return _luu(fig, duong_dan)


def ve_mang_ky_nang(M, assoc, communities, duong_dan, toi_da_nut=40, npmi_toi_thieu=0.1):
    """Mạng đồng xuất hiện: nút = skill (to theo số tin), cạnh = cặp đạt ngưỡng,
    độ dày theo NPMI. Bốn cộng đồng lớn nhất có màu riêng, còn lại gộp xám."""
    import networkx as nx
    if assoc.empty:
        return None
    G = nx.Graph()
    for a, b, v in assoc[["skill_a", "skill_b", "npmi"]].itertuples(index=False):
        if v > npmi_toi_thieu:            # bỏ cạnh gần-độc-lập, tránh thành búi len
            G.add_edge(a, b, w=float(v))
    if G.number_of_nodes() == 0:
        return None
    tan_so = M.sum()
    giu = sorted(G.nodes, key=lambda s: -tan_so.get(s, 0))[:toi_da_nut]
    G = G.subgraph(giu).copy()
    G.remove_nodes_from([n for n in list(G.nodes) if G.degree(n) == 0])
    if G.number_of_nodes() == 0:
        return None

    co_lon = pd.Series([communities.get(n) for n in G.nodes]).value_counts().index[:len(MAU)]
    mau_cong_dong = {c: MAU[i] for i, c in enumerate(co_lon)}
    mau = [mau_cong_dong.get(communities.get(n), MAU_KHAC) for n in G.nodes]
    kich_thuoc = [40 + 400 * tan_so[n] / tan_so.max() for n in G.nodes]

    pos = nx.spring_layout(G, weight="w", seed=42, k=1.2 / max(1, G.number_of_nodes()) ** 0.5)
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#c9c8c3",
                           width=[0.5 + 2.5 * G[u][v]["w"] for u, v in G.edges])
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=mau, node_size=kich_thuoc,
                           edgecolors="white", linewidths=1)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=7, font_color="#0b0b0b",
                            labels={n: _nhan_ngan(n, 20) for n in G.nodes})
    from matplotlib.lines import Line2D
    chu_thich = [Line2D([], [], marker="o", ls="", color=MAU[i], label=f"Cộng đồng {c}")
                 for i, c in enumerate(co_lon)]
    if MAU_KHAC in mau:
        chu_thich.append(Line2D([], [], marker="o", ls="", color=MAU_KHAC, label="Cộng đồng khác"))
    ax.legend(handles=chu_thich, fontsize=8, frameon=False, labelcolor=MUC_XAM, loc="lower left")
    ax.set_title(f"RQ2 — mạng đồng xuất hiện kỹ năng (cạnh: NPMI > {npmi_toi_thieu}, ≥ {MIN_COOC} lần; "
                 "nút to = nhiều tin)",
                 fontsize=10, color="#0b0b0b")
    ax.axis("off")
    fig.tight_layout()
    return _luu(fig, duong_dan)


# ------------------------------------------------------------------ RQ3

def ve_do_phan_tan(dispersion, duong_dan):
    """Mỗi title: độ phân tán skill thực tế (chấm) so với vùng 5–95% của các nhóm
    bốc ngẫu nhiên cùng cỡ (vạch xám). Chấm nằm TRÁI vạch = title nhất quán thật."""
    d = dispersion.sort_values("dispersion").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8, 0.35 * len(d) + 1.8))
    fig.patch.set_facecolor("#fcfcfb")
    y = list(range(len(d)))
    if {"baseline_p5", "baseline_p95"} <= set(d.columns):
        ax.hlines(y, d["baseline_p5"], d["baseline_p95"], color="#d8d7d2", linewidth=6,
                  label="ngẫu nhiên cùng cỡ (5–95%)")
        ax.scatter(d["baseline_mean"], y, marker="|", s=90, color=MUC_NHAT)
    co = d["informative"].astype(bool) if "informative" in d.columns else pd.Series(True, index=d.index)
    if co.any():
        ax.scatter(d.loc[co, "dispersion"], [y[i] for i in d.index[co]], s=55, color=MAU[0],
                   edgecolors="white", linewidths=0.8, zorder=3, label="nhất quán hơn ngẫu nhiên")
    if (~co).any():
        ax.scatter(d.loc[~co, "dispersion"], [y[i] for i in d.index[~co]], s=55, color=MAU[1],
                   marker="s", edgecolors="white", linewidths=0.8, zorder=3,
                   label="không khác ngẫu nhiên")
    ax.set_yticks(y, [f"{_nhan_ngan(t)}  (n={n})" for t, n in zip(d["title"], d["n_postings"])],
                  fontsize=8)
    ax.set_xlabel("độ phân tán = 1 − Jaccard TB giữa các tin cùng title (thấp = nhất quán)",
                  fontsize=9, color=MUC_XAM)
    ax.set_title("RQ3 — title có thống nhất về kỹ năng hơn ngẫu nhiên không?", fontsize=11, color="#0b0b0b")
    _dinh_dang_truc(ax)
    ax.tick_params(axis="y", colors=MUC_XAM)
    ax.legend(fontsize=8, frameon=False, labelcolor=MUC_XAM, loc="upper center",
              bbox_to_anchor=(0.5, -0.12 - 0.6 / max(len(d), 1)), ncol=3)
    fig.tight_layout()
    return _luu(fig, duong_dan)


def ve_dendrogram_title(profile_matrix, duong_dan):
    """Cây phân cấp các title theo hồ sơ skill (khoảng cách cosine, liên kết average)."""
    from scipy.cluster.hierarchy import dendrogram, linkage
    if len(profile_matrix) < 2:
        return None
    Z = linkage(profile_matrix.values, method="average", metric="cosine")
    fig, ax = plt.subplots(figsize=(8, 0.35 * len(profile_matrix) + 1.4))
    fig.patch.set_facecolor("#fcfcfb")
    dendrogram(Z, labels=[_nhan_ngan(t, 34) for t in profile_matrix.index], orientation="right",
               ax=ax, color_threshold=0, above_threshold_color=MAU[0], leaf_font_size=8)
    ax.set_xlabel("khoảng cách cosine giữa hồ sơ skill", fontsize=9, color=MUC_XAM)
    ax.set_title("RQ3 — title nào gần nhau về kỹ năng", fontsize=11, color="#0b0b0b")
    _dinh_dang_truc(ax)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return _luu(fig, duong_dan)


def _ma_tran_title(similarity):
    ten = sorted(set(similarity["title_a"]) | set(similarity["title_b"]))
    S = pd.DataFrame(1.0, index=ten, columns=ten)
    for a, b, c in similarity[["title_a", "title_b", "cosine"]].itertuples(index=False):
        S.loc[a, b] = S.loc[b, a] = c
    return S


def ve_heatmap_title(similarity, duong_dan):
    """Ma trận cosine giữa các title (một thang tuần tự 0 -> 1)."""
    if similarity.empty:
        return None
    S = _ma_tran_title(similarity)
    fig, ax = plt.subplots(figsize=(0.45 * len(S) + 3, 0.45 * len(S) + 2.2))
    fig.patch.set_facecolor("#fcfcfb")
    anh = ax.imshow(S.values, cmap=TUAN_TU, vmin=0, vmax=1)
    nhan = [_nhan_ngan(t, 22) for t in S.index]
    ax.set_xticks(range(len(S)), nhan, rotation=60, ha="right", fontsize=7)
    ax.set_yticks(range(len(S)), nhan, fontsize=7)
    ax.tick_params(colors=MUC_XAM, length=0)
    for canh in ax.spines.values():
        canh.set_visible(False)
    if len(S) <= 15:
        for i in range(len(S)):
            for j in range(len(S)):
                if i != j:
                    v = S.values[i, j]
                    ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6,
                            color="white" if v > 0.6 else "#0b0b0b")
    thanh = fig.colorbar(anh, ax=ax, shrink=0.7)
    thanh.set_label("cosine hồ sơ skill", fontsize=8, color=MUC_XAM)
    thanh.ax.tick_params(labelsize=7, colors=MUC_NHAT)
    ax.set_title("RQ3 — độ giống nhau giữa các title", fontsize=11, color="#0b0b0b")
    fig.tight_layout()
    return _luu(fig, duong_dan)


def ve_ho_so_title(profile_matrix, duong_dan, top=15):
    """Title × skill: tỉ lệ tin của title yêu cầu skill (top skill theo tổng)."""
    if profile_matrix.empty:
        return None
    cot = profile_matrix.mean().sort_values(ascending=False).head(top).index
    P = profile_matrix[cot]
    fig, ax = plt.subplots(figsize=(0.5 * len(cot) + 3.5, 0.4 * len(P) + 2.2))
    fig.patch.set_facecolor("#fcfcfb")
    anh = ax.imshow(P.values, cmap=TUAN_TU, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(cot)), [_nhan_ngan(s, 16) for s in cot], rotation=60, ha="right", fontsize=7)
    ax.set_yticks(range(len(P)), [_nhan_ngan(t, 30) for t in P.index], fontsize=7)
    ax.tick_params(colors=MUC_XAM, length=0)
    for canh in ax.spines.values():
        canh.set_visible(False)
    thanh = fig.colorbar(anh, ax=ax, shrink=0.7)
    thanh.set_label("tỉ lệ tin của title có yêu cầu skill", fontsize=8, color=MUC_XAM)
    thanh.ax.tick_params(labelsize=7, colors=MUC_NHAT)
    ax.set_title("RQ3 — hồ sơ kỹ năng của từng title", fontsize=11, color="#0b0b0b")
    fig.tight_layout()
    return _luu(fig, duong_dan)


# ------------------------------------------------------------------ RQ4

def ve_cum_x_title(crosstab, duong_dan, toi_da_title=25):
    """Heatmap cụm × title: mỗi hàng (title) chia theo tỉ lệ sang các cụm.

    Title nằm gọn trong một cụm = tên nghề khớp cấu trúc dữ liệu; trải đều = lệch.
    """
    if crosstab.empty:
        return None
    ct = crosstab.loc[crosstab.sum(axis=1).sort_values(ascending=False).index[:toi_da_title]]
    ty_le = ct.div(ct.sum(axis=1), axis=0)
    fig, ax = plt.subplots(figsize=(0.6 * ct.shape[1] + 4, 0.32 * len(ct) + 1.8))
    fig.patch.set_facecolor("#fcfcfb")
    anh = ax.imshow(ty_le.values, cmap=TUAN_TU, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(ct.shape[1]), [f"Cụm {c}" for c in ct.columns], fontsize=8)
    ax.set_yticks(range(len(ct)), [f"{_nhan_ngan(t, 30)}  (n={int(n)})" for t, n in ct.sum(axis=1).items()],
                  fontsize=7)
    ax.tick_params(colors=MUC_XAM, length=0)
    for canh in ax.spines.values():
        canh.set_visible(False)
    thanh = fig.colorbar(anh, ax=ax, shrink=0.7)
    thanh.set_label("tỉ lệ tin của title rơi vào cụm", fontsize=8, color=MUC_XAM)
    thanh.ax.tick_params(labelsize=7, colors=MUC_NHAT)
    ax.set_title("RQ4 — mỗi title rơi vào những cụm nào", fontsize=11, color="#0b0b0b")
    fig.tight_layout()
    return _luu(fig, duong_dan)
