"""CLI xuất đặc trưng và đánh giá parser."""
import argparse
import json
from pathlib import Path

from .features import export_features
from .skill_extractor import DEFAULT_TAXONOMY


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("preview", "extract"):
        item = sub.add_parser(command)
        item.add_argument("--input", type=Path, required=True)
        item.add_argument("--output-dir", type=Path, required=True)
        item.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    item = sub.add_parser("evaluate")
    item.add_argument("--gold", type=Path, required=True)
    item.add_argument("--output-dir", type=Path, required=True)
    item.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    item.add_argument("--reference", type=Path, default=Path(__file__).resolve().parents[2] / "data/sample/sample_jobs.jsonl")
    args = parser.parse_args()
    try:
        if args.command == "evaluate":
            from .evaluation import evaluate_file
            report = evaluate_file(args.gold, args.output_dir, args.taxonomy, args.reference)
        else:
            preview = args.command == "preview"
            if preview and args.output_dir.resolve().name != "development":
                raise ValueError("Preview phải nằm trong thư mục development để phân biệt artifact chính thức.")
            prefix = "sample_" if preview else ""
            report = export_features(args.input, args.output_dir / f"{prefix}job_skills.parquet",
                                     args.output_dir / f"{prefix}job_skill_matrix.parquet", args.taxonomy, preview=preview)
            (args.output_dir / f"{prefix}manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    except (ValueError, OSError) as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
