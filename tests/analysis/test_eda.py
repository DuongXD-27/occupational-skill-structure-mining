"""EDA: các hàm phân loại và đo trên dữ liệu nhỏ tự dựng."""
import pandas as pd

from src.analysis import eda


def test_language_of():
    assert eda.language_of("Phân tích dữ liệu bán hàng và xây dựng báo cáo định kỳ") == "Tiếng Việt"
    assert eda.language_of("Build data pipelines with Spark and Airflow") == "Tiếng Anh"
    assert eda.language_of("1234 --") == "Không rõ"


def test_seniority_and_title_group():
    assert eda.seniority_of("Senior Data Engineer") == "Senior"
    assert eda.seniority_of("AI Engineer Intern") == "Intern / Thực tập"
    assert eda.seniority_of("Data Analyst") == "Không ghi cấp bậc"
    assert eda.title_group("Machine Learning Engineer") == "Chức danh Data/AI"
    assert eda.title_group("IT Business Analyst") == "Business Analyst"
    assert eda.title_group("Backend Engineer (Golang)") == "IT chung và khác"


def test_missing_counts_not_available_as_missing():
    raw = pd.DataFrame({f: ["x", "x", "x"] for f in eda.SCHEMA_RAW})
    raw["raw_location"] = ["Hà Nội", "Not Available", "Not Available, Not Available"]
    raw["raw_experience"] = [None, "", "2 năm"]
    m = eda.missing_by_field(raw).set_index("field")["missing"]
    assert m["raw_location"] == 2 and m["raw_experience"] == 2 and m["company"] == 0


def test_skill_profile_core_share():
    prof, group = eda.skill_profile(["Python, SQL, Power BI and Machine Learning", "Nothing here"],
                                    "taxonomy/skills_taxonomy.csv")
    assert prof.loc[0, "n_skills"] >= 3 and 0 < prof.loc[0, "core_share"] <= 1
    assert prof.loc[1, "n_skills"] == 0 and prof.loc[1, "core_share"] == 0
