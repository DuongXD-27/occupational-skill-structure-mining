"""Adapter chỉ chuyển tham số sang API đã có của thành viên."""

from .config import PipelineError, StageContext


def cleaner(context: StageContext):
    # API quan sát trên origin/feature/data-cleaner-rq1; không sao chép logic QR.
    try:
        from src.cleaner.pipeline import run_pipeline
    except ModuleNotFoundError as exc:
        if exc.name in ("src.cleaner", "src.cleaner.pipeline"):
            raise PipelineError("Chưa bàn giao cleaner vào nhánh hiện tại: thiếu src.cleaner.pipeline.") from exc
        raise

    return run_pipeline(
        input_path=context.paths["raw"],
        output_path=context.paths["clean"],
        **context.options,
    )
