"""Chạy RQ2–RQ4 và ghi bảng/biểu đồ vào một thư mục; trả trạng thái từng RQ.

Dùng chung cho:
- `scripts/run_analysis.py` (dòng lệnh, dữ liệu giả hoặc thật);
- pipeline tích hợp: entry point `src.analysis.report:run` (report/main.tex §4.1),
  trả `{"RQ2": ..., "RQ3": ..., "RQ4": ...}` với `status` là `completed` hoặc `skipped`.

RQ nào chưa đủ điều kiện theo analysis_spec §7–§8 thì `skipped` kèm lý do và không
ghi bảng kết quả, để không có con số nào bị công bố khi mẫu quá nhỏ.
"""
from pathlib import Path

import pandas as pd

from . import config, loaders, plots, quality, rq2, rq3, rq4


def _write(table, out_dir, name, written, log):
    path = Path(out_dir) / f"{name}.csv"
    table.to_csv(path, index=False, encoding="utf-8-sig")
    written.append(path.name)
    log(f"  {path}   ({len(table)} dòng)")


def _plot(fn, out_dir, name, files, log, *args):
    """Vẽ một hình; hàm vẽ trả None khi không đủ dữ liệu để vẽ."""
    path = fn(*args, Path(out_dir) / name)
    if path:
        files.append(name)
        log(f"  {path}")


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
        _write(r2["top_pairs"], out, "rq2_top_pairs_by_metric", files, log)
        _plot(plots.ve_heatmap_lien_ket, out, "rq2_association_heatmap.png", files, log, M, r2["pairs"])
        _plot(plots.ve_mang_ky_nang, out, "rq2_cooccurrence_network.png", files, log,
              M, r2["pairs"], r2["communities"])
    else:
        log(f"  Không cặp skill nào đạt {config.MIN_COOCCURRENCE} lần đồng xuất hiện — "
            "bỏ bảng cặp và cộng đồng skill")
    _write(r2["negative_pairs"], out, "rq2_negative_pairs", files, log)
    _plot(plots.ve_top_skill, out, "rq2_top_skills.png", files, log, r2["skill_frequency"])
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
        _write(r3["profiles"], out, "rq3_title_profiles", files, log)
        _write(r3["flagged"], out, "rq3_flagged_pairs", files, log)
        _plot(plots.ve_do_phan_tan, out, "rq3_dispersion_vs_baseline.png", files, log, r3["dispersion"])
        _plot(plots.ve_dendrogram_title, out, "rq3_title_dendrogram.png", files, log, r3["profile_matrix"])
        _plot(plots.ve_heatmap_title, out, "rq3_title_similarity.png", files, log, r3["title_similarity"])
        _plot(plots.ve_ho_so_title, out, "rq3_title_profiles.png", files, log, r3["profile_matrix"])
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
        _write(pd.concat([r4["labels"], r4["hierarchical_labels"]], axis=1).reset_index(),
               out, "rq4_cluster_assignment", files, log)
        _write(r4["examples"], out, "rq4_cluster_examples", files, log)
        _write(r4["method_comparison"], out, "rq4_method_comparison", files, log)
        _write(pd.DataFrame([r4["method_agreement"]]), out, "rq4_method_agreement", files, log)
        _write(r4["pca"], out, "rq4_pca_coordinates", files, log)
        if "unblinded" in r4:
            _write(r4["profiles"].merge(r4["unblinded"], on="cluster"), out, "rq4_clusters_with_titles", files, log)
            _write(pd.DataFrame([r4["agreement"]]), out, "rq4_agreement", files, log)
            _write(r4["crosstab"].reset_index(), out, "rq4_cluster_title_crosstab", files, log)
            _plot(plots.ve_cum_x_title, out, "rq4_cluster_title_heatmap.png", files, log, r4["crosstab"])
        log(f"  {plots.ve_pca(r4, titles, out / 'rq4_pca.png')}")
        log(f"  {plots.ve_quet_k(r4['sweep'], r4['chosen_k'], out / 'rq4_sweep_k.png')}")
        files += ["rq4_pca.png", "rq4_sweep_k.png"]
        status["RQ4"] = {"status": "completed", "artifacts": files}

    return status


def load_titles(clean_path):
    """normalized_job_title của các tin hợp lệ (relevance=true, duplicate=false)."""
    ok = quality.valid_records(_read_table(clean_path))
    return ok.set_index("job_id")["normalized_job_title"]


def _read_table(path):
    return pd.read_parquet(path) if str(path).endswith(".parquet") else pd.read_json(path, lines=True)


def run_quality_checks(clean_path, skills_path, out_dir, log=print):
    """Chạy 8 kiểm tra (src/analysis/quality.py), ghi quality_checks.csv, trả danh sách lỗi."""
    checks = quality.run_checks(_read_table(clean_path), _read_table(skills_path))
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    _write(checks, out_dir, "quality_checks", [], log)
    return quality.failed(checks)


def run(context):
    """Entry point cho src.pipeline (bước `analysis`).

    Tám kiểm tra chất lượng chạy trước (spec §9). Có kiểm tra thất bại thì RQ2–RQ4
    đều `skipped` kèm lý do — trừ khi options `enforce_quality_checks` = false
    (chỉ dùng khi thử pipeline trên dữ liệu mẫu, không bao giờ cho lần chạy research).
    """
    paths = context.paths
    options = dict(context.options)
    loi = run_quality_checks(paths["clean"], paths["skills"], paths["analysis"], log=lambda *_: None)
    if loi and options.get("enforce_quality_checks", True):
        reason = "kiểm tra chất lượng thất bại (quality_checks.csv): " + "; ".join(loi)
        return {rq: {"status": "skipped", "reason": reason, "artifacts": []} for rq in ("RQ2", "RQ3", "RQ4")}
    M = loaders.load_skill_matrix(paths["matrix"], taxonomy_path=paths["taxonomy"])
    titles = load_titles(paths["clean"])
    return write_analysis(
        M, titles, paths["analysis"], log=lambda *_: None,
        stability_iterations=options.get("stability_iterations", config.STABILITY_ITERATIONS),
    )
