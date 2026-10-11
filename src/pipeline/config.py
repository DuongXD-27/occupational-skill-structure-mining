"""Đọc cấu hình JSON; đường dẫn tương đối luôn tính từ file cấu hình."""

from dataclasses import dataclass
import json
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


class PipelineError(ValueError):
    """Lỗi cấu hình, bàn giao module hoặc hợp đồng dữ liệu."""


STAGES = ("clean", "rq1", "extract", "analysis")
PATH_KEYS = ("raw", "clean", "skills", "matrix", "taxonomy", "rq1", "analysis", "report")


@dataclass(frozen=True)
class Config:
    file: Path
    run_kind: str
    paths: Mapping[str, Path]
    modules: Mapping[str, str | None]
    options: Mapping[str, dict]


@dataclass(frozen=True)
class StageContext:
    stage: str
    paths: Mapping[str, Path]
    options: Mapping


def load_config(path: str | Path) -> Config:
    file = Path(path).resolve()
    try:
        data = json.loads(file.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise PipelineError(f"Không đọc được cấu hình {file}: {exc}") from exc
    if not isinstance(data, dict) or data.get("version") != 1:
        raise PipelineError("Cấu hình phải là object JSON với version = 1.")
    run_kind = data.get("run_kind", "integration")
    if run_kind not in ("integration", "research"):
        raise PipelineError("run_kind phải là integration hoặc research.")
    raw_paths = data.get("paths")
    if not isinstance(raw_paths, dict):
        raise PipelineError("Cấu hình thiếu object paths.")
    paths = {}
    for key in PATH_KEYS:
        value = raw_paths.get(key)
        if not isinstance(value, str) or not value.strip():
            raise PipelineError(f"Cấu hình thiếu đường dẫn paths.{key}.")
        paths[key] = (file.parent / value).resolve()
    # Chặn ghi đè input hoặc đầu ra khác, kể cả đường dẫn lồng nhau.
    for i, key in enumerate(PATH_KEYS):
        for other in PATH_KEYS[i + 1:]:
            a, b = paths[key], paths[other]
            if a == b or a in b.parents or b in a.parents:
                raise PipelineError(f"paths.{key} và paths.{other} trùng/lồng nhau: {a}, {b}")
    for key in ("raw", "clean", "skills", "matrix"):
        if paths[key].suffix.lower() not in (".jsonl", ".parquet"):
            raise PipelineError(f"paths.{key} phải là file .jsonl hoặc .parquet.")
    if paths["raw"].suffix.lower() != ".jsonl":
        raise PipelineError("paths.raw phải là file .jsonl theo hợp đồng crawler.")
    if paths["taxonomy"].suffix.lower() != ".csv" or paths["report"].suffix.lower() != ".json":
        raise PipelineError("paths.taxonomy phải là .csv; paths.report phải là .json.")
    modules = data.get("modules", {})
    options = data.get("options", {})
    if not isinstance(modules, dict) or not isinstance(options, dict):
        raise PipelineError("modules và options phải là object JSON.")
    for stage in STAGES:
        entry = modules.get(stage)
        if entry is not None and (not isinstance(entry, str) or entry.count(":") != 1):
            raise PipelineError(f"modules.{stage} phải là module:function hoặc null.")
        if not isinstance(options.get(stage, {}), dict):
            raise PipelineError(f"options.{stage} phải là object JSON.")
    return Config(file, run_kind, MappingProxyType(paths), MappingProxyType(modules), options)
