"""Tám kiểm tra chất lượng chạy TRƯỚC mọi phân tích (analysis_spec §9).

Đặc tả nói "tám kiểm tra" nhưng không liệt kê; danh sách dưới đây là ĐỀ XUẤT
chờ Leader duyệt (ngưỡng ở config.py). Ý chung: bắt những lỗi kỹ thuật làm kết
quả nghiêng đúng về phía kết luận nhóm đang chờ đợi — trích xuất yếu làm danh
sách skill ngắn, danh sách ngắn làm mọi tin trông khác nhau, thổi phồng độ phân
tán (RQ3) và làm yếu mọi liên kết (RQ2).

Hợp đồng pipeline (src/pipeline/contracts.py) đã chặn lỗi cấu trúc: đủ 22 trường,
ma trận khớp extracted_skills, ô 0/1. Các kiểm tra ở đây đo CHẤT LƯỢNG nội dung,
nên vẫn có ích khi chạy ngoài pipeline (scripts/run_analysis.py).

Một kiểm tra thất bại -> RQ2–RQ4 bị `skipped`, trả việc về khâu thu thập/làm sạch/
trích xuất; không con số nào được đưa vào báo cáo.
"""
import hashlib

import pandas as pd

from . import config


def valid_records(clean):
    return clean[(clean["relevance_flag"] == True) & (clean["duplicate_flag"] == False)]  # noqa: E712


def _skill_list(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return list(v)


def _text(row):
    return " ".join(str(row.get(c) or "") for c in ("job_description", "job_requirements")).strip()


def run_checks(clean, skills):
    """clean: bảng sạch 22 trường; skills: bảng (job_id, extracted_skills, skill_count)
    do bước trích xuất xuất ra. Trả DataFrame một dòng mỗi kiểm tra."""
    ok = valid_records(clean)
    n = len(ok)
    sk = skills.set_index("job_id")
    rows = []

    def add(code, name, value, threshold, passed, detail=""):
        rows.append({"check": code, "name": name, "value": value, "threshold": threshold,
                     "passed": bool(passed), "detail": detail})

    # QC1 — mọi tin hợp lệ đều có dòng skill, không thừa, không thiếu
    ids_ok, ids_skill = set(ok["job_id"]), set(sk.index)
    thieu, thua = ids_ok - ids_skill, ids_skill - ids_ok
    add("QC1", "job_id khớp giữa bảng sạch và bảng skill", len(thieu) + len(thua), "0 lệch",
        not thieu and not thua and sk.index.is_unique,
        f"thiếu {len(thieu)}, thừa {len(thua)}, trùng {int(sk.index.duplicated().sum())}")

    lists = sk.reindex(sorted(ids_ok & ids_skill))["extracted_skills"].map(_skill_list)

    # QC2 — null = bộ trích xuất chưa chạy (khác [] = tin viết kém), spec §2
    so_null = int(lists.isna().sum())
    add("QC2", "extracted_skills không null", so_null, "0", so_null == 0)

    lens = lists.dropna().map(len)
    # QC3 — trích xuất quá yếu
    tb = round(float(lens.mean()), 2) if len(lens) else 0.0
    add("QC3", "số skill trung bình mỗi tin", tb, f"≥ {config.QC_MIN_MEAN_SKILLS}",
        tb >= config.QC_MIN_MEAN_SKILLS, f"trung vị {lens.median() if len(lens) else 0}")

    # QC4 — quá nhiều tin không bắt được skill nào
    ty_le_0 = round(float((lens == 0).mean()), 4) if len(lens) else 1.0
    add("QC4", "tỉ lệ tin không có skill", ty_le_0, f"≤ {config.QC_MAX_ZERO_SKILL_SHARE}",
        ty_le_0 <= config.QC_MAX_ZERO_SKILL_SHARE)

    # QC5 — skill có mặt gần như mọi tin: alias quá rộng hoặc bắt nhầm từ chung
    dem = pd.Series([s for l in lists.dropna() for s in set(l)]).value_counts()
    top_share = round(float(dem.iloc[0] / len(lens)), 4) if len(dem) and len(lens) else 0.0
    add("QC5", "tỉ lệ tin của skill phổ biến nhất", top_share, f"≤ {config.QC_MAX_SKILL_SHARE}",
        top_share <= config.QC_MAX_SKILL_SHARE, str(dem.index[0]) if len(dem) else "")

    # QC6 — trùng còn sót sau bước khử trùng (cùng công ty + title chuẩn + nội dung)
    if n:
        khoa = ok.apply(lambda r: (str(r.get("company") or "").strip().lower(),
                                   str(r.get("normalized_job_title") or "").strip().lower(),
                                   hashlib.sha1(" ".join(_text(r).lower().split()).encode()).hexdigest()),
                        axis=1)
        so_trung = int(khoa.duplicated().sum())
    else:
        so_trung = 0
    ty_le_trung = round(so_trung / n, 4) if n else 0.0
    add("QC6", "tỉ lệ trùng còn sót trong tin hợp lệ", ty_le_trung,
        f"≤ {config.QC_MAX_RESIDUAL_DUP_SHARE}", ty_le_trung <= config.QC_MAX_RESIDUAL_DUP_SHARE,
        f"{so_trung} tin")

    # QC7 — crawler lấy thiếu nội dung: văn bản quá ngắn thì không có gì để trích skill
    do_dai = ok.apply(lambda r: len(_text(r)), axis=1) if n else pd.Series(dtype=int)
    trung_vi = int(do_dai.median()) if n else 0
    add("QC7", "độ dài trung vị mô tả + yêu cầu (ký tự)", trung_vi,
        f"≥ {config.QC_MIN_MEDIAN_TEXT_CHARS}", trung_vi >= config.QC_MIN_MEDIAN_TEXT_CHARS)

    # QC8 — RQ1/RQ3/RQ4 đều cần title chuẩn hoá; tin thiếu title bị lặng lẽ rơi khỏi so sánh
    thieu_title = int(ok["normalized_job_title"].map(lambda t: not str(t or "").strip()).sum()) if n else 0
    add("QC8", "tin hợp lệ thiếu normalized_job_title", thieu_title, "0", thieu_title == 0)

    return pd.DataFrame(rows)


def failed(checks):
    bad = checks[~checks["passed"]]
    return [f"{r.check} {r.name} = {r.value} (cần {r.threshold})" for r in bad.itertuples()]
