"""Toàn bộ ngưỡng và tham số của phần phân tích nằm ở đây.

analysis_spec_v0.1.md cam kết không để con số nào nằm rải rác trong code.
File này chính là cam kết đó.

Mọi giá trị bên dưới đều là ĐỀ XUẤT, spec ghi rõ là provisional — phải chờ
leader duyệt. Khi đổi, chỉ sửa ở đây, không sửa trong rq2/rq3/rq4.
"""

RANDOM_SEED = 42

# --- RQ2: ngưỡng cho skill và cặp skill (spec mục 7) ---
MIN_SKILL_COUNT = 3        # skill xuất hiện ít hơn 3 tin thì coi là nhiễu
MIN_COOCCURRENCE = 5       # dưới 5 lần cùng xuất hiện, chỉ số lift nhảy loạn

# --- RQ3: ngưỡng cho title và tin (spec mục 7) ---
MIN_POSTINGS_PER_TITLE = 5     # 5 tin cho ra 10 cặp để so sánh
MIN_SKILLS_PER_POSTING = 2     # 1 skill thì không có gì để so
BOOTSTRAP_ITERATIONS = 1000    # số lần bốc nhóm ngẫu nhiên cho mỗi title

# --- RQ4: phân cụm (spec mục 6 và 7) ---
MIN_POSTINGS_FOR_CLUSTERING = 300   # dưới mức này, cụm tìm được là ngẫu nhiên
K_MIN, K_MAX = 2, 15                # khoảng quét số cụm
STABILITY_ITERATIONS = 100          # số vòng lấy mẫu lại cho mỗi k
STABILITY_SAMPLE_FRAC = 0.8         # mỗi vòng giữ lại 80% dữ liệu
STABILITY_TIE_MARGIN = 0.02         # chênh trong khoảng này thì coi là hòa
SILHOUETTE_TIE_MARGIN = 0.02        # hòa tiếp thì mới lấy k nhỏ hơn
