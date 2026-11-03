"""Chạy RQ2–RQ4 và ghi bảng/biểu đồ vào một thư mục; trả trạng thái từng RQ.

Dùng chung cho:
- `scripts/run_analysis.py` (dòng lệnh, dữ liệu giả hoặc thật);
- pipeline tích hợp: entry point `src.analysis.report:run` (docs/pipeline/README.md §5),
  trả `{"RQ2": ..., "RQ3": ..., "RQ4": ...}` với `status` là `completed` hoặc `skipped`.

RQ nào chưa đủ điều kiện theo analysis_spec §7–§8 thì `skipped` kèm lý do và không
ghi bảng kết quả, để không có con số nào bị công bố khi mẫu quá nhỏ.
"""
from pathlib import Path

import pandas as pd

from . import config, loaders, plots, rq2, rq3, rq4


def _write(table, out_dir, name, written, log):
    path = Path(out_dir) / f"{name}.csv"
    table.to_csv(path, index=False, encoding="utf-8-sig")
    written.append(path.name)
    log(f"  {path}   ({len(table)} dòng)")


def write_analysis(M, titles, out_dir, log=print, stability_iterations=config.STABILITY_ITERATIONS):
    """Chạy RQ2, RQ3, RQ4 trên ma trận M (job_id ở index, cột là tên skill)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    status = {}

    # ------------------------------------------------------------- RQ2
    log("RQ2 — nhu cầu và cấu trúc kỹ năng")
    r2 = rq2.run_rq2(M)
    files = []
    _write(r2["skill_frequency"], out, "rq2_skill_frequency", files, log)
    _write(pd.DataFrame([r2["skills_per_posting"]]), out, "rq2_skills_per_posting", files, log)
    if not r2["pairs"].empty:
        _write(r2["pairs"], out, "rq2_skill_pairs", files, log)
        _write(pd.DataFrame(sorted(r2["communities"].items(), key=lambda kv: (kv[1], kv[0])),
                            columns=["skill", "community"]), out, "rq2_skill_communities", files, log)
    else:
        log(f"  Không cặp skill nào đạt {config.MIN_COOCCURRENCE} lần đồng xuất hiện — "
            "bỏ bảng cặp và cộng đồng skill")
    status["RQ2"] = {"status": "completed", "artifacts": files}

    # ------------------------------------------------------------- RQ3
    log("\nRQ3 — độ nhất quán giữa title và skill")
    r3 = rq3.run_rq3(M, titles)
    if r3["status"] != "ok":
        log(f"  BỎ QUA: {r3['status']}")
        status["RQ3"] = {"status": "skipped", "reason": f"RQ3: {r3['status']}", "artifacts": []}
    else:
        files = []
        _write(r3["dispersion"], out, "rq3_title_dispersion", files, log)
        _write(r3["title_similarity"], out, "rq3_title_similarity", files, log)
        _write(r3["notable"], out, "rq3_notable_pairs", files, log)
        if r3.get("skipped_titles") is not None and len(r3["skipped_titles"]):
            _write(r3["skipped_titles"], out, "rq3_skipped_titles", files, log)
        status["RQ3"] = {"status": "completed", "artifacts": files}

    # ------------------------------------------------------------- RQ4
    log("\nRQ4 — cấu trúc nghề nghiệp hình thành từ dữ liệu")
    r4 = rq4.run_rq4(M, titles=titles, stability_iterations=stability_iterations)
    log(f"  {r4['message']}")
    if r4["status"] == "skipped":
        status["RQ4"] = {"status": "skipped", "reason": r4["message"], "artifacts": []}
    else:
        files = []
        log(f"  Chọn k = {r4['chosen_k']}")
        _write(r4["sweep"], out, "rq4_k_sweep", files, log)
        _write(r4["profiles"], out, "rq4_cluster_profiles", files, log)
        _write(r4["labels"].reset_index(), out, "rq4_cluster_assignment", files, log)
        _write(r4["pca"], out, "rq4_pca_coordinates", files, log)
        if "unblinded" in r4:
            _write(r4["profiles"].merge(r4["unblinded"], on="cluster"), out, "rq4_clusters_with_titles", files, log)
            _write(pd.DataFrame([r4["agreement"]]), out, "rq4_agreement", files, log)
        log(f"  {plots.ve_pca(r4, titles, out / 'rq4_pca.png')}")
        log(f"  {plots.ve_quet_k(r4['sweep'], r4['chosen_k'], out / 'rq4_sweep_k.png')}")
        files += ["rq4_pca.png", "rq4_sweep_k.png"]
        status["RQ4"] = {"status": "completed", "artifacts": files}

    return status


def load_titles(clean_path):
    """normalized_job_title của các tin hợp lệ (relevance=true, duplicate=false)."""
    clean = pd.read_parquet(clean_path) if str(clean_path).endswith(".parquet") else pd.read_json(clean_path, lines=True)
    ok = clean[(clean["relevance_flag"] == True) & (clean["duplicate_flag"] == False)]  # noqa: E712
    return ok.set_index("job_id")["normalized_job_title"]


def run(context):
    """Entry point cho src.pipeline (bước `analysis`)."""
    paths = context.paths
    M = loaders.load_skill_matrix(paths["matrix"], taxonomy_path=paths["taxonomy"])
    titles = load_titles(paths["clean"])
    options = dict(context.options)
    return write_analysis(
        M, titles, paths["analysis"], log=lambda *_: None,
        stability_iterations=options.get("stability_iterations", config.STABILITY_ITERATIONS),
    )
