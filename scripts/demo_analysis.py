"""Chạy toàn bộ phân tích trên dữ liệu giả rồi in kết quả.

    python scripts/demo_analysis.py

Đây là cách nhanh nhất để thấy ba module cho ra cái gì. Nó dùng tin giả có
cấu trúc biết trước (4 nghề), nên có thể đối chiếu kết quả với đáp án thay vì
đoán xem nó trông có hợp lý không.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis import rq2, rq3, rq4, synthetic

pd.set_option("display.width", 200)


def banner(text):
    print(f"\n{'=' * 70}\n{text}\n{'=' * 70}")


# ------------------------------------------------------------- dữ liệu
df = synthetic.generate_jobs(n=400)
M = synthetic.build_matrix(df)
titles = df.set_index("job_id")["normalized_job_title"]

banner("THE DATA")
print(f"{len(M)} postings x {M.shape[1]} skills, all values 0 or 1")
print("\nFirst 3 postings:")
cot = ["job_id", "normalized_job_title", "extracted_skills"]
print(df[cot].head(3).to_string(index=False))
print("\nSame 3 as the matrix the analyses actually read:")
print(M.head(3).iloc[:, :8].to_string())

# ----------------------------------------------------------------- RQ2
banner("RQ2 - WHICH SKILLS ARE IN DEMAND")
r2 = rq2.run_rq2(M)
print("Skills per posting:", r2["skills_per_posting"])
print("\nTop 5 skills:")
print(r2["skill_frequency"].head(5).to_string(index=False))

print("\nStrongest pairs (by npmi):")
print(r2["pairs"].head(5).to_string(index=False))

p = r2["pairs"]
trap = p[((p.skill_a == "Python") & (p.skill_b == "SQL")) |
         ((p.skill_a == "SQL") & (p.skill_b == "Python"))]
if not trap.empty:
    print("\nThe trap - Python and SQL:")
    print(trap.to_string(index=False))
    print("High joint count, negative npmi: they meet often only because both")
    print("are everywhere. Counting alone would have called them related.")

# ----------------------------------------------------------------- RQ3
banner("RQ3 - DO TITLES MATCH THE SKILLS")
r3 = rq3.run_rq3(M, titles, iterations=200)
print("Same title, different skills (higher = the title says less):")
print(r3["dispersion"].to_string(index=False))
print("\ninformative=True means the title scored below the random baseline,")
print("so it carries more information than a random label would.")

print("\nDifferent titles, same skills:")
print(r3["title_similarity"].head(5).to_string(index=False))

print("\nNotable pairs - what they share, what tells them apart:")
pd.set_option("display.max_colwidth", 45)
print(r3["notable"].to_string(index=False))
print("\nAn empty 'chi_title_a'/'chi_title_b' means the two names ask for")
print("exactly the same skills - two names, one job.")

# ----------------------------------------------------------------- RQ4
banner("RQ4 - LET THE ALGORITHM GROUP THE JOBS")

small = synthetic.build_matrix(synthetic.generate_jobs(n=250))
print("With 250 postings:")
print(" ", rq4.run_rq4(small)["message"])

print("\nWith 400 postings:")
out = rq4.run_rq4(M, titles=df.set_index("job_id")["true_family"],
                  stability_iterations=20)
print(" ", out["message"])

print("\nSweep across k:")
print(out["sweep"].head(7).to_string(index=False))
print(f"\nChosen k = {out['chosen_k']}   (4 families were planted)")

print("\nWhat each cluster is made of - titles still hidden at this point:")
print(out["profiles"].to_string(index=False))

print("\nOnly now are the titles joined back:")
print(out["unblinded"].to_string(index=False))
print("\nAgreement with the planted families:", out["agreement"])
print("ARI near 1 means the algorithm rediscovered the structure it never saw.")
