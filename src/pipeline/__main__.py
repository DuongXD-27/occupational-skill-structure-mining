"""CLI: python -m src.pipeline --config ... --stage clean|rq1|extract|analysis|all."""

import argparse
import json
import sys

from .config import PipelineError, STAGES
from .runner import run_pipeline


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Điều phối pipeline Data/AI và kiểm tra schema.")
    parser.add_argument("--config", default="config/pipeline.json")
    parser.add_argument("--stage", choices=("all", *STAGES), default="all")
    args = parser.parse_args()
    try:
        report = run_pipeline(args.config, args.stage)
    except PipelineError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({"status": report["status"], "counts": report["counts"], "rq": report["rq"]},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
