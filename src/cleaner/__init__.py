"""
src/cleaner/__init__.py
Cleaning pipeline package for the occupational-skill-structure-mining project.
Exports the public API used by the pipeline adapter, RQ1 and tests.
"""

from .location import normalize_location
from .title import normalize_title
from .relevance import classify_relevance
from .duplicates import detect_duplicates, detect_exact_duplicates, detect_near_duplicates
from .pipeline import run_pipeline
from .rq1 import compute_rq1, write_rq1

__all__ = [
    "normalize_location",
    "normalize_title",
    "classify_relevance",
    "detect_duplicates",
    "detect_exact_duplicates",
    "detect_near_duplicates",
    "run_pipeline",
    "compute_rq1",
    "write_rq1",
]
