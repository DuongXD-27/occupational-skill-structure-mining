"""Chuyển bản giao của bước bóc skill về đúng một dạng mà các module RQ cần.

Ba module RQ đều giả định: ma trận tin x skill, job_id nằm ở index, tên cột là
tên skill, trong ô chỉ có 0 và 1. Không có gì bảo đảm bản giao sẽ đúng dạng
đó, nên việc chuyển đổi và kiểm tra gom hết về đây, làm một lần, thay vì mỗi
module lại tự xoay xở.

Khác biệt đã biết giữa `data_schema_v1.md` và thứ module cần:

  Schema mục 14   job_id là một CỘT; cột skill đặt tên skill_001, skill_002,
                  ... tham chiếu tới taxonomy
  Module cần      job_id ở INDEX; cột đặt tên Python, PyTorch, ...

Để nguyên mã số thì kết quả không ai đọc nổi — "cluster top skills:
skill_047, skill_112" chẳng nói lên điều gì — nên dùng `skills_taxonomy.csv`
để ánh xạ ngược về tên.
"""
import re

import pandas as pd

from . import config

NON_SKILL_COLUMNS = {"job_id", "skill_count", "source", "crawl_timestamp",
                     "parser_version", "taxonomy_version"}


class MatrixProblem(ValueError):
    """Ném ra khi bản giao không phân tích được như hiện trạng."""


# định danh tin tuyển dụng, theo mọi cách đặt tên có thể gặp
ID_COLUMNS = ("job_id", "jobid", "id", "posting_id", "vacancy_id", "doc_id")

# skill_001, sk_001, s_001, skill001 — một tiền tố cộng chữ số
CODE_PATTERN = re.compile(r"^[a-z_]{1,8}_?\d{2,}$", re.IGNORECASE)


def _looks_like_a_code(name):
    """Cột này là mã khó đọc hay là tên skill đọc được?"""
    return bool(CODE_PATTERN.match(str(name)))


def _set_job_id_index(df):
    """Đưa định danh tin lên index, dù nó được đặt tên là gì.

    Sai chỗ này vừa âm thầm vừa đắt: không có nó thì index thành số thứ tự
    dòng, mọi nhãn cụm và toạ độ PCA mất liên kết với tin tuyển dụng, không
    ghép ngược lại được với tin thật nào cả.
    """
    if df.index.name in ID_COLUMNS:
        df.index.name = "job_id"
        return df

    found = [c for c in df.columns if str(c).lower() in ID_COLUMNS]
    if found:
        df = df.set_index(found[0])
        df.index.name = "job_id"
        return df

    # a non-numeric first column with one distinct value per row is an id
    first = df.columns[0]
    if df[first].dtype == object and df[first].nunique() == len(df):
        df = df.set_index(first)
        df.index.name = "job_id"
        return df

    raise MatrixProblem(
        "No posting identifier found. Expected one of "
        f"{', '.join(ID_COLUMNS)} as a column or as the index; "
        f"got columns {list(df.columns[:6])}... "
        "Without it, results cannot be traced back to a posting.")


def load_taxonomy(path="taxonomy/skills_taxonomy.csv"):
    """Đọc taxonomy, trả về {mã: tên chuẩn}.

    Schema không cố định tên cột, nên lấy cột đầu tiên trông giống mã và cột
    đầu tiên trông giống tên.
    """
    tax = pd.read_csv(path)
    cols = {c.lower(): c for c in tax.columns}

    code_col = next((cols[c] for c in ("skill_id", "skill_code", "code", "id")
                     if c in cols), tax.columns[0])
    name_col = next((cols[c] for c in ("skill_name", "canonical_name", "name", "skill")
                     if c in cols), tax.columns[1])

    return dict(zip(tax[code_col].astype(str), tax[name_col].astype(str)))


def load_skill_matrix(path="data/features/job_skill_matrix.parquet",
                      taxonomy_path="taxonomy/skills_taxonomy.csv",
                      min_skill_count=config.MIN_SKILL_COUNT):
    """Đọc ma trận bản giao, trả về đúng dạng các module cần.

    Xử lý được: job_id nằm ở cột hay ở index; cột là mã skill_001 hay tên
    thật; ô kiểu bool, float hay int; cột thừa không phải skill.
    """
    df = pd.read_parquet(path)
    df = _set_job_id_index(df)

    # bỏ mọi cột không phải skill
    df = df.drop(columns=NON_SKILL_COLUMNS, errors="ignore")

    # mã kiểu skill_001 đổi thành tên đọc được, nếu taxonomy có
    if any(_looks_like_a_code(c) for c in df.columns):
        try:
            mapping = load_taxonomy(taxonomy_path)
        except FileNotFoundError:
            mapping = {}
        df = df.rename(columns=lambda c: mapping.get(str(c), str(c)))

    # ô kiểu bool / float / chuỗi đưa hết về 0 và 1
    df = df.apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)

    validate_matrix(df)
    return df.loc[:, df.sum() >= min_skill_count]


def load_from_job_skills(path="data/features/job_skills.parquet",
                         min_skill_count=config.MIN_SKILL_COUNT):
    """Dựng ma trận từ file dạng dài thay thế.

    Dùng khi thiếu `job_skill_matrix.parquet` nhưng có `job_skills.parquet`
    — gồm job_id và một danh sách skill.
    """
    df = pd.read_parquet(path)
    if "extracted_skills" not in df.columns:
        raise MatrixProblem(
            f"{path} has no `extracted_skills` column. Found: {list(df.columns)}")

    rows = df.set_index("job_id")["extracted_skills"]
    rows = rows.apply(lambda v: [] if v is None else list(v))

    skills = sorted({s for row in rows for s in row})
    if not skills:
        raise MatrixProblem(
            f"{path}: `extracted_skills` is empty on every record. "
            "The extractor has not run yet.")

    M = pd.DataFrame([[1 if s in set(row) else 0 for s in skills] for row in rows],
                     index=rows.index, columns=skills, dtype=int)
    M.index.name = "job_id"
    validate_matrix(M)
    return M.loc[:, M.sum() >= min_skill_count]


def validate_matrix(M):
    """Báo lỗi to và rõ, thay vì cho ra một con số sai.

    Mỗi phép kiểm tra ở đây ứng với một cách mà phân tích có thể cho ra kết
    quả trông rất hợp lý nhưng thực chất vô nghĩa.
    """
    problems = []

    if M.empty:
        problems.append("the matrix has no rows")
    if M.shape[1] == 0:
        problems.append("the matrix has no skill columns")

    bad = sorted(set(pd.unique(M.values.ravel())) - {0, 1})
    if bad:
        problems.append(f"cells must be 0 or 1, found {bad[:5]}")

    if M.index.duplicated().any():
        n = int(M.index.duplicated().sum())
        problems.append(f"{n} job_id values appear more than once")

    if (M.sum(axis=1) == 0).all():
        problems.append("every posting has zero skills — the extractor produced nothing")

    if problems:
        raise MatrixProblem("Cannot analyse this matrix: " + "; ".join(problems))

    return warn_about(M)


def warn_about(M):
    """Những thứ không chặn phân tích nhưng làm thay đổi cách đọc kết quả.

    Trả về chứ không in ra, để notebook tự quyết hiển thị cái gì.
    """
    notes = []
    counts = M.sum(axis=1)

    thin = int((counts < config.MIN_SKILLS_PER_POSTING).sum())
    if thin:
        notes.append(f"{thin} postings have fewer than "
                     f"{config.MIN_SKILLS_PER_POSTING} skills; they count in skill "
                     "frequency but are excluded from similarity and clustering")

    if counts.mean() < 3:
        notes.append(f"mean skills per posting is {counts.mean():.1f} — below 3 suggests "
                     "weak extraction, which inflates dispersion and weakens every "
                     "association")

    if len(M) < config.MIN_POSTINGS_FOR_CLUSTERING:
        notes.append(f"{len(M)} postings is below the {config.MIN_POSTINGS_FOR_CLUSTERING} "
                     "needed for RQ4")

    if any(_looks_like_a_code(c) for c in M.columns):
        notes.append("some columns are still taxonomy codes, not names — "
                     "results will be hard to read")

    return notes


def check_titles(titles, M, min_postings=config.MIN_POSTINGS_PER_TITLE):
    """Cột title có dùng được cho RQ3 không?

    Trả về (ok, message). RQ3 cần một title có đủ tin đứng sau; không có thì
    bên trong chẳng còn gì để so sánh.
    """
    t = titles.reindex(M.index)

    if t.isna().all():
        return False, "normalized_job_title is empty on every posting"

    missing = int(t.isna().sum())
    counts = t.value_counts()
    qualifying = int((counts >= min_postings).sum())

    if qualifying == 0:
        return False, (f"no title reaches {min_postings} postings "
                       f"(largest group: {int(counts.max())}). RQ3 cannot run")

    msg = f"{qualifying} titles reach {min_postings} postings"
    if missing:
        msg += f"; {missing} postings have no title"
    return True, msg
