"""Sinh tin tuyển dụng giả, biết trước đáp án.

Vì sao cần: Cường chưa bóc skill xong, mà dữ liệu thật thì không cho mình biết
kết quả đúng là gì. Ở đây mình tự đặt cấu trúc trước, rồi xem thuật toán có
tìm lại được đúng cấu trúc đó không.

Chú ý: `Python` và `SQL` cố tình nằm ở nhiều nghề. Đây là cái bẫy — một cặp
skill hay xuất hiện cùng nhau chỉ vì cả hai đều phổ biến thì KHÔNG phải là
cặp liên quan, và RQ2 phải phân biệt được.
"""
import numpy as np
import pandas as pd

from . import config

# Bốn nhóm nghề, mỗi nhóm có bộ skill lõi riêng. Đây là ĐÁP ÁN.
FAMILIES = {
    "computer_vision": {
        "core": ["Python", "PyTorch", "OpenCV", "Computer Vision", "YOLO"],
        "titles": ["Computer Vision Engineer", "AI Engineer", "ML Engineer"],
    },
    "llm": {
        "core": ["Python", "LLM", "RAG", "Vector Database", "LangChain"],
        "titles": ["AI Engineer", "GenAI Engineer", "ML Engineer"],
    },
    "data_engineering": {
        "core": ["Python", "SQL", "Spark", "Airflow", "AWS", "Kafka"],
        "titles": ["Data Engineer", "Senior Data Engineer"],
    },
    "data_analysis": {
        "core": ["SQL", "Power BI", "Excel", "Tableau", "Statistics"],
        "titles": ["Data Analyst", "Business Intelligence Analyst"],
    },
}

# Skill không thuộc nghề nào — nhiễu thuần, để bài toán khó lên
FILLER = ["Git", "Docker", "Linux", "Agile", "English", "Jira", "Communication"]


def generate_jobs(n=400, noise=0.15, drop=0.2, seed=config.RANDOM_SEED):
    """Sinh `n` tin tuyển dụng từ các nghề khai báo ở trên.

    noise: xác suất thêm một skill lạc từ nghề khác
    drop : xác suất bỏ bớt một skill lõi (tin thật thường không liệt kê đủ)

    Trả về DataFrame gồm job_id, true_family, normalized_job_title,
    extracted_skills. Cột `true_family` là đáp án — RQ4 tuyệt đối không được
    nhìn thấy nó khi phân cụm.
    """
    rng = np.random.default_rng(seed)
    fam_names = list(FAMILIES)
    all_core = sorted({s for f in FAMILIES.values() for s in f["core"]})

    rows = []
    for i in range(n):
        fam = fam_names[i % len(fam_names)]
        spec = FAMILIES[fam]

        skills = [s for s in spec["core"] if rng.random() > drop]
        # tin nào cũng có vài skill chung chung, giống quảng cáo thật
        skills += list(rng.choice(FILLER, size=rng.integers(1, 3), replace=False))
        # thỉnh thoảng lẫn một skill vốn thuộc nghề khác
        if rng.random() < noise:
            skills.append(str(rng.choice(all_core)))

        rows.append({
            "job_id": f"job_{i:04d}",
            "true_family": fam,
            "normalized_job_title": str(rng.choice(spec["titles"])),
            "extracted_skills": sorted(set(skills)),
        })

    return pd.DataFrame(rows)


def build_matrix(df, min_skill_count=config.MIN_SKILL_COUNT):
    """Chuyển thành bảng tin x skill, ô bằng 1 nếu tin đó yêu cầu skill đó.

    Mọi phân tích phía sau chỉ đọc bảng này, không đọc gì khác.
    Skill dưới ngưỡng bị loại ngay tại đây, một lần, không loại lại ở từng
    module.
    """
    skills = sorted({s for row in df["extracted_skills"] for s in row})
    M = pd.DataFrame(
        [[1 if s in set(row) else 0 for s in skills] for row in df["extracted_skills"]],
        index=df["job_id"], columns=skills, dtype=int,
    )
    return M.loc[:, M.sum() >= min_skill_count]
