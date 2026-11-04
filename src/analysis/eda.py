"""Phân tích khám phá dữ liệu (EDA) trên bảng thô đã gộp và bảng sạch.

Trả lời các câu hỏi "dữ liệu trông như thế nào" trước khi tin vào RQ1–RQ4:
thiếu gì, văn bản dài ngắn ra sao, tiếng Việt hay tiếng Anh, đăng khi nào,
công ty nào chiếm nhiều tin, kỹ năng phân bố thế nào, và tin bị giữ/bị loại
khác nhau ở đâu (để kiểm tra bộ lọc liên quan).

    python -m src.analysis.eda --raw data/raw/jobs_raw.jsonl \\
        --clean data/processed/jobs_clean.parquet --out reports/eda

Mọi con số là tổng hợp; không xuất văn bản tin tuyển dụng ra ngoài.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .plots import MAU, MUC_NHAT, MUC_XAM, _dinh_dang_truc, _luu  # noqa: E402

XAM = "#c9c8c3"
SCHEMA_RAW = ["source_job_id", "raw_job_title", "company", "raw_location", "posted_date",
              "raw_experience", "job_description", "job_requirements"]

# Nhóm kỹ năng "lõi Data/AI" trong taxonomy (phần còn lại là kỹ năng phát triển phần mềm,
# hạ tầng, bảo mật, công cụ chung)
DATA_AI_GROUPS = {
    "Data Analysis & BI", "Data Engineering & Architecture",
    "Machine Learning, Statistics & Optimization", "Generative AI & Agentic Systems",
    "NLP, Vision & Multimodal AI", "Distributed, Streaming & Big Data",
    "Data Quality, Testing & Observability", "Applied Analytics & Business Platforms",
}

# Phân loại thô theo chức danh — chỉ để mô tả, không thay cho bộ lọc liên quan
_DATA_AI_TITLE = re.compile(
    r"data|dữ liệu|\bai\b|a\.i\.|\bml\b|machine learning|học máy|mlops|llm|genai|generative|"
    r"\bbi\b|business intelligence|analytics|scientist|\bnlp\b|computer vision|deep learning|"
    r"trí tuệ nhân tạo|big data|thống kê|statistic", re.IGNORECASE)
_BA_TITLE = re.compile(r"business analyst|\bba\b|phân tích nghiệp vụ|nghiệp vụ", re.IGNORECASE)

_SENIORITY = [
    ("Intern / Thực tập", r"\bintern(ship)?\b|thực tập"),
    ("Fresher / Junior", r"\bfresher\b|\bjunior\b|\bjr\.?\b|\bentry\b"),
    ("Middle", r"\bmid(dle)?\b"),
    ("Senior", r"\bsenior\b|\bsr\.?\b"),
    ("Lead / Principal", r"\blead\b|\bprincipal\b|\bstaff\b|\btrưởng nhóm\b"),
    ("Manager / Head", r"\bmanager\b|\bhead\b|\bdirector\b|\bchief\b|\bcto\b|\btrưởng phòng\b|\bgiám đốc\b"),
]

_VI_CHARS = set("ăâđêôơưàáạảãằắặẳẵầấậẩẫèéẹẻẽềếệểễìíịỉĩòóọỏõồốộổỗờớợởỡùúụủũừứựửữỳýỵỷỹ")


# ---------------------------------------------------------------- đọc dữ liệu

def read_table(path):
    path = str(path)
    if path.endswith(".parquet"):
        return pd.read_parquet(path)
    return pd.DataFrame([json.loads(l) for l in open(path, encoding="utf-8") if l.strip()], dtype=object)


def _text(df):
    return (df["job_description"].fillna("").astype(str) + "\n" + df["job_requirements"].fillna("").astype(str)).str.strip()


# ---------------------------------------------------------------- các phép đo

def missing_by_field(raw, fields=SCHEMA_RAW):
    """Tỷ lệ thiếu từng trường thô. 'Not Available' do trang ghi cũng tính là thiếu."""
    rows = []
    for f in fields:
        s = raw[f] if f in raw else pd.Series([None] * len(raw))
        miss = s.isna() | s.astype(str).str.strip().isin(["", "None", "nan"]) | \
            s.astype(str).str.fullmatch(r"(Not Available[, ]*)+", case=False)
        rows.append({"field": f, "missing": int(miss.sum()), "share": round(float(miss.mean()), 4)})
    return pd.DataFrame(rows)


def language_of(text):
    """Tiếng Việt / Trộn / Tiếng Anh theo tỷ lệ chữ có dấu tiếng Việt (ước lượng thô)."""
    letters = [c for c in text.lower() if c.isalpha()]
    if not letters:
        return "Không rõ"
    r = sum(c in _VI_CHARS for c in letters) / len(letters)
    return "Tiếng Việt" if r >= 0.05 else ("Trộn Việt–Anh" if r >= 0.005 else "Tiếng Anh")


def seniority_of(title):
    t = str(title or "")
    for name, pat in _SENIORITY:
        if re.search(pat, t, re.IGNORECASE):
            return name
    return "Không ghi cấp bậc"


def title_group(title):
    t = str(title or "")
    if _DATA_AI_TITLE.search(t):
        return "Chức danh Data/AI"
    if _BA_TITLE.search(t):
        return "Business Analyst"
    return "IT chung và khác"


def status_of(clean):
    rel, dup = clean["relevance_flag"] == True, clean["duplicate_flag"] == True  # noqa: E712
    return np.where(~rel, "Bị loại (ngoài phạm vi)", np.where(dup, "Bị loại (trùng)", "Hợp lệ"))


def skill_profile(texts, taxonomy_path):
    """Chạy bộ trích xuất trên MỌI tin (kể cả tin bị loại) để so sánh nhóm giữ/loại."""
    from src.parser.skill_extractor import SkillExtractor
    ex = SkillExtractor(taxonomy_path)
    group = {r["canonical_name"]: r["skill_group"] for r in ex.rows}
    out = []
    for t in texts:
        skills = ex.extract(t)
        core = sum(group.get(s) in DATA_AI_GROUPS for s in skills)
        out.append({"skills": skills, "n_skills": len(skills), "n_core": core,
                    "core_share": core / len(skills) if skills else 0.0})
    return pd.DataFrame(out), group


def build_frame(raw, clean, taxonomy_path):
    """Một bảng một dòng mỗi tin: các trường mô tả + trạng thái + hồ sơ kỹ năng."""
    df = clean.copy()
    df["status"] = status_of(df)
    df["text"] = _text(df)
    df["text_len"] = df["text"].str.len()
    df["language"] = df["text"].map(language_of)
    df["seniority"] = df["raw_job_title"].map(seniority_of)
    df["title_group"] = df["raw_job_title"].map(title_group)
    df["round"] = np.where(df["parser_version"].astype(str) == "v0.2", "Pilot 30/09", "Đợt 03/11")
    df["posted"] = pd.to_datetime(df["posted_date"], errors="coerce")
    prof, group = skill_profile((df["raw_job_title"].fillna("") + "\n" + df["text"]).tolist(), taxonomy_path)
    df = pd.concat([df.reset_index(drop=True), prof], axis=1)
    return df, group


def summary(df):
    ok = df[df.status == "Hợp lệ"]
    comp = ok["company"].value_counts()
    return pd.DataFrame([
        ("Tin thô sau gộp", len(df)),
        ("Tin hợp lệ", len(ok)),
        ("Công ty khác nhau (tin hợp lệ)", comp.size),
        ("Tỷ trọng 10 công ty đăng nhiều nhất", round(float(comp.head(10).sum() / len(ok)), 4)),
        ("Công ty chỉ đăng 1 tin", int((comp == 1).sum())),
        ("Độ dài văn bản trung vị (ký tự, tin hợp lệ)", int(ok.text_len.median())),
        ("Số kỹ năng trung bình (tin hợp lệ)", round(float(ok.n_skills.mean()), 2)),
        ("Tỷ lệ kỹ năng lõi Data/AI trung vị (tin hợp lệ)", round(float(ok.core_share.median()), 3)),
        ("Ngày đăng sớm nhất", str(df.posted.min().date())),
        ("Ngày đăng muộn nhất", str(df.posted.max().date())),
    ], columns=["metric", "value"])


# ---------------------------------------------------------------- hình

def _bar_h(ax, labels, values, fmt, accent_first=0, color=None):
    y = np.arange(len(labels))[::-1]
    cols = [MAU[0] if i < accent_first else (color or XAM) for i in range(len(labels))]
    ax.barh(y, values, color=cols, height=0.7)
    ax.set_yticks(y, labels, fontsize=8.5, color=MUC_XAM)
    for yi, v in zip(y, values):
        ax.text(v, yi, " " + fmt(v), va="center", fontsize=8, color=MUC_XAM)
    _dinh_dang_truc(ax)
    ax.grid(axis="y", visible=False)


def fig_missing(miss, path):
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    d = miss.sort_values("share", ascending=False)
    _bar_h(ax, d["field"], d["share"] * 100, lambda v: f"{v:.0f}%", accent_first=0, color=MAU[1])
    ax.set_xlim(0, 115)
    ax.set_xlabel("% tin thô bị thiếu (504 tin)", fontsize=9, color=MUC_XAM)
    ax.set_title("Địa điểm và kinh nghiệm là hai trường thiếu nhiều nhất", fontsize=11)
    fig.tight_layout()
    return _luu(fig, path)


def fig_text_length(df, path):
    fig, ax = plt.subplots(figsize=(8, 3.6))
    bins = np.logspace(np.log10(max(50, df.text_len.min())), np.log10(df.text_len.max() + 1), 30)
    for name, c in (("Hợp lệ", MAU[0]), ("Bị loại (ngoài phạm vi)", MAU[1])):
        s = df.loc[df.status == name, "text_len"]
        ax.hist(s, bins=bins, color=c, alpha=0.55, label=f"{name} (n={len(s)}, trung vị {int(s.median()):,} ký tự)".replace(",", "."))
    ax.set_xscale("log")
    ax.set_xlabel("độ dài mô tả + yêu cầu (ký tự, thang log)", fontsize=9, color=MUC_XAM)
    ax.set_ylabel("số tin", fontsize=9, color=MUC_XAM)
    ax.set_title("Phần lớn tin dài 1.500–5.000 ký tự, đủ để trích kỹ năng", fontsize=11)
    _dinh_dang_truc(ax)
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    return _luu(fig, path)


def fig_language_seniority(df, path):
    ok = df[df.status == "Hợp lệ"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 3.4))
    lang = ok.language.value_counts()
    _bar_h(a, lang.index, lang.values / len(ok) * 100, lambda v: f"{v:.0f}%", accent_first=1)
    a.set_xlim(0, 100)
    a.set_title("Ngôn ngữ của tin (ước lượng theo chữ có dấu)", fontsize=10)
    order = [n for n, _ in _SENIORITY] + ["Không ghi cấp bậc"]
    sen = ok.seniority.value_counts().reindex(order).fillna(0)
    _bar_h(b, sen.index, sen.values / len(ok) * 100, lambda v: f"{v:.0f}%")
    b.set_xlim(0, 100)
    b.set_title("Cấp bậc ghi trong chức danh", fontsize=10)
    fig.suptitle("Tin hợp lệ (n=%d)" % len(ok), fontsize=11)
    fig.tight_layout()
    return _luu(fig, path)


def fig_posted(df, path):
    fig, ax = plt.subplots(figsize=(8.5, 3.4))
    d = df.dropna(subset=["posted"]).copy()
    d["week"] = d.posted.dt.to_period("W").dt.start_time
    tab = d.pivot_table(index="week", columns="round", values="job_id", aggfunc="count").fillna(0)
    bottom = np.zeros(len(tab))
    for i, col in enumerate(["Pilot 30/09", "Đợt 03/11"]):
        if col in tab:
            ax.bar(tab.index, tab[col], width=5, bottom=bottom, color=MAU[i], label=col, alpha=0.85)
            bottom += tab[col].values
    for x, lab in ((pd.Timestamp("2026-09-30"), "thu pilot"), (pd.Timestamp("2026-11-03"), "thu đợt 2")):
        ax.axvline(x, color=MUC_NHAT, ls="--", lw=1)
        ax.text(x, ax.get_ylim()[1] * 0.95, " " + lab, fontsize=8, color=MUC_XAM, va="top")
    ax.set_ylabel("số tin theo tuần đăng", fontsize=9, color=MUC_XAM)
    ax.set_title("Mỗi đợt thu chủ yếu bắt tin đăng trong khoảng 6 tuần trước đó", fontsize=11)
    _dinh_dang_truc(ax)
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    fig.autofmt_xdate()
    fig.tight_layout()
    return _luu(fig, path)


def fig_companies(df, path, top=15):
    ok = df[df.status == "Hợp lệ"]
    c = ok.company.fillna("(không rõ)").value_counts().head(top)
    fig, ax = plt.subplots(figsize=(7.5, 0.28 * top + 1.2))
    _bar_h(ax, [s if len(s) <= 38 else s[:37] + "…" for s in c.index], c.values, lambda v: f"{int(v)}")
    ax.set_xlabel("số tin hợp lệ", fontsize=9, color=MUC_XAM)
    ax.set_title(f"{top} công ty đăng nhiều tin nhất", fontsize=11)
    fig.tight_layout()
    return _luu(fig, path)


def fig_skills_per_posting(df, path):
    ok = df[df.status == "Hợp lệ"]
    fig, ax = plt.subplots(figsize=(8, 3.3))
    ax.hist(ok.n_skills, bins=range(0, int(ok.n_skills.max()) + 2), color=MAU[0], alpha=0.85)
    m = ok.n_skills.median()
    ax.axvline(m, color=MUC_XAM, ls="--", lw=1)
    ax.text(m, ax.get_ylim()[1] * 0.95, f" trung vị {m:.0f}", fontsize=8, color=MUC_XAM, va="top")
    ax.set_xlabel("số kỹ năng tìm được trong một tin", fontsize=9, color=MUC_XAM)
    ax.set_ylabel("số tin", fontsize=9, color=MUC_XAM)
    ax.set_title("Đa số tin có 3–15 kỹ năng; một số tin liệt kê trên 30", fontsize=11)
    _dinh_dang_truc(ax)
    fig.tight_layout()
    return _luu(fig, path)


def fig_skill_groups(df, group, path):
    ok = df[df.status == "Hợp lệ"]
    groups = sorted(set(group.values()))
    share = {g: float(ok.skills.map(lambda ss: any(group.get(s) == g for s in ss)).mean()) for g in groups}
    s = pd.Series(share).sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4.6))
    y = np.arange(len(s))[::-1]
    ax.barh(y, s.values * 100, color=[MAU[0] if g in DATA_AI_GROUPS else XAM for g in s.index], height=0.7)
    ax.set_yticks(y, s.index, fontsize=8.5, color=MUC_XAM)
    for yi, v in zip(y, s.values * 100):
        ax.text(v, yi, f" {v:.0f}%", va="center", fontsize=8, color=MUC_XAM)
    ax.set_xlim(0, 100)
    ax.set_xlabel("% tin hợp lệ yêu cầu ít nhất một kỹ năng của nhóm (xanh: nhóm lõi Data/AI)", fontsize=9, color=MUC_XAM)
    ax.set_title("Nhóm kỹ năng được yêu cầu trong tin hợp lệ", fontsize=11)
    _dinh_dang_truc(ax)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return _luu(fig, path)


def fig_filter_check(df, path):
    """Tỷ lệ kỹ năng lõi Data/AI theo nhóm chức danh: chỗ bộ lọc liên quan đang lọt."""
    ok = df[df.status == "Hợp lệ"]
    groups = [("Chức danh Data/AI", ok[ok.title_group == "Chức danh Data/AI"]),
              ("Business Analyst", ok[ok.title_group == "Business Analyst"]),
              ("IT chung và khác", ok[ok.title_group == "IT chung và khác"]),
              ("Tin bị loại (ngoài phạm vi)", df[df.status == "Bị loại (ngoài phạm vi)"])]
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    data = [g.core_share.values * 100 for _, g in groups]
    try:
        bp = ax.boxplot(data, orientation="horizontal", widths=0.55, patch_artist=True, showfliers=False)
    except TypeError:  # matplotlib < 3.10
        bp = ax.boxplot(data, vert=False, widths=0.55, patch_artist=True, showfliers=False)
    for i, b in enumerate(bp["boxes"]):
        b.set(facecolor=(MAU[0] if i == 0 else XAM), alpha=0.5, edgecolor=MUC_XAM)
    for m in bp["medians"]:
        m.set(color="#0b0b0b", lw=1.5)
    rng = np.random.default_rng(0)
    for i, d in enumerate(data, 1):
        ax.scatter(d, i + rng.uniform(-0.18, 0.18, len(d)), s=6, color=MUC_XAM, alpha=0.5, zorder=3)
    ax.set_yticks(range(1, len(groups) + 1), [f"{n} (n={len(g)})" for n, g in groups], fontsize=8.5, color=MUC_XAM)
    ax.invert_yaxis()
    ax.set_xlabel("% kỹ năng của tin thuộc nhóm lõi Data/AI", fontsize=9, color=MUC_XAM)
    ax.set_title("Tin IT chung đang được giữ có ít kỹ năng Data/AI hơn cả tin bị loại", fontsize=10.5)
    _dinh_dang_truc(ax)
    fig.tight_layout()
    return _luu(fig, path)


# ---------------------------------------------------------------- chạy

def run(raw_path, clean_path, taxonomy_path, out_dir, log=print):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw, clean = read_table(raw_path), read_table(clean_path)
    df, group = build_frame(raw, clean, taxonomy_path)
    miss = missing_by_field(raw)
    tables = {
        "eda_summary": summary(df),
        "eda_missing_by_field": miss,
        "eda_status_by_round": pd.crosstab(df["round"], df["status"]).reset_index(),
        "eda_language": df.groupby(["status", "language"]).size().reset_index(name="n"),
        "eda_seniority": df[df.status == "Hợp lệ"].seniority.value_counts().reset_index(),
        "eda_top_companies": df[df.status == "Hợp lệ"].company.value_counts().head(30).reset_index(),
        "eda_title_group_profile": df.groupby(["status", "title_group"]).agg(
            n=("job_id", "size"), median_text_len=("text_len", "median"), mean_skills=("n_skills", "mean"),
            median_core_share=("core_share", "median")).round(3).reset_index(),
    }
    for name, t in tables.items():
        t.to_csv(out / f"{name}.csv", index=False, encoding="utf-8-sig")
        log(f"  {out / name}.csv  ({len(t)} dòng)")
    figs = [fig_missing(miss, out / "eda_missing.png"), fig_text_length(df, out / "eda_text_length.png"),
            fig_language_seniority(df, out / "eda_language_seniority.png"), fig_posted(df, out / "eda_posted_dates.png"),
            fig_companies(df, out / "eda_top_companies.png"), fig_skills_per_posting(df, out / "eda_skills_per_posting.png"),
            fig_skill_groups(df, group, out / "eda_skill_groups.png"), fig_filter_check(df, out / "eda_filter_check.png")]
    for f in figs:
        log(f"  {f}")
    return df, tables


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default="data/raw/jobs_raw.jsonl")
    ap.add_argument("--clean", default="data/processed/jobs_clean.parquet")
    ap.add_argument("--taxonomy", default="taxonomy/skills_taxonomy.csv")
    ap.add_argument("--out", default="reports/eda")
    a = ap.parse_args(argv)
    run(a.raw, a.clean, a.taxonomy, a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
