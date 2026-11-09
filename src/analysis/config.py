"""Toàn bộ ngưỡng và tham số của phần phân tích nằm ở đây.

Báo cáo (report/main.tex §4.5) cam kết không để con số nào nằm rải rác trong code.
File này chính là cam kết đó.

Leader đã duyệt giữ nguyên các ngưỡng ngày 2026-11-03 (report/main.tex
phụ lục B, mục F). Khi đổi, ghi lý do và chỉ sửa ở đây, không sửa
trong rq2/rq3/rq4.
"""

RANDOM_SEED = 42

# --- RQ2: ngưỡng cho skill và cặp skill (spec mục 7) ---
MIN_SKILL_COUNT = 3        # skill xuất hiện ít hơn 3 tin thì coi là nhiễu
MIN_COOCCURRENCE = 5       # dưới 5 lần cùng xuất hiện, chỉ số lift nhảy loạn

# --- RQ3: ngưỡng cho title và tin (spec mục 7) ---
MIN_POSTINGS_PER_TITLE = 5     # 5 tin cho ra 10 cặp để so sánh
MIN_TITLES_FOR_RQ3 = 3         # chốt 2026-11-03: dưới 3 title đạt ngưỡng thì không báo cáo RQ3
MIN_SKILLS_PER_POSTING = 2     # 1 skill thì không có gì để so
BOOTSTRAP_ITERATIONS = 1000    # số lần bốc nhóm ngẫu nhiên cho mỗi title

# --- RQ4: phân cụm (spec mục 6 và 7) ---
MIN_POSTINGS_FOR_CLUSTERING = 300   # dưới mức này, cụm tìm được là ngẫu nhiên
K_MIN, K_MAX = 2, 15                # khoảng quét số cụm
STABILITY_ITERATIONS = 100          # số vòng lấy mẫu lại cho mỗi k
STABILITY_SAMPLE_FRAC = 0.8         # mỗi vòng giữ lại 80% dữ liệu
STABILITY_TIE_MARGIN = 0.02         # chênh trong khoảng này thì coi là hòa
SILHOUETTE_TIE_MARGIN = 0.02        # hòa tiếp thì mới lấy k nhỏ hơn

# --- RQ2: bảng xếp hạng (spec mục 4) ---
TOP_PAIRS_PER_METRIC = 30           # "Top 30 cặp kỹ năng theo từng thước đo"
TOP_SKILLS_CHART = 30               # biểu đồ top 30 kỹ năng
HEATMAP_SKILLS = 20                 # số skill phổ biến nhất trên heatmap liên kết

# --- RQ3: ba ngưỡng cảnh báo cặp title giống nhau (spec mục 5, "3 ngưỡng").
# Đặc tả chưa ghi giá trị; đây là đề xuất chờ Leader duyệt.
TITLE_SIMILARITY_THRESHOLDS = (0.70, 0.80, 0.90)

# --- RQ4: phân cụm phân cấp để so sánh với K-Means (phạm vi bắt buộc §11) ---
HIERARCHICAL_METRIC = "jaccard"     # khoảng cách hợp với vector skill nhị phân
HIERARCHICAL_LINKAGE = "average"    # ward chỉ hợp với khoảng cách Euclid

# --- 8 kiểm tra chất lượng trước phân tích (spec mục 9).
# Đặc tả nói "tám kiểm tra" nhưng chưa liệt kê; danh sách và ngưỡng ở
# src/analysis/quality.py là đề xuất chờ Leader duyệt.
QC_MIN_MEAN_SKILLS = 3.0            # TB < 3 skill/tin: trích xuất yếu (spec mục 4)
QC_MAX_ZERO_SKILL_SHARE = 0.10      # > 10% tin không có skill nào
QC_MAX_RESIDUAL_DUP_SHARE = 0.02    # > 2% tin hợp lệ còn trùng (công ty + title + mô tả)
QC_MAX_SKILL_SHARE = 0.90           # skill có ở > 90% tin: alias quá rộng hoặc bắt nhầm từ chung
QC_MIN_MEDIAN_TEXT_CHARS = 300      # mô tả + yêu cầu quá ngắn: crawler lấy thiếu nội dung
