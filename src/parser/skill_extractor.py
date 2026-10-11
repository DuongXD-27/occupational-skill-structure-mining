"""Trích xuất từ taxonomy; dùng chung cho recount và pipeline."""
from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

FIELDNAMES = [
    "skill_id",
    "canonical_name",
    "abbreviation",
    "aliases",
    "skill_group",
    "observed_count",
]
TEXT_FIELDS = ("raw_job_title", "job_description", "job_requirements")
AMBIGUOUS_ABBREVIATION_CONTEXT = {
    "CV": (
        "computer vision",
        "opencv",
        "image processing",
        "image recognition",
        "object detection",
        "video processing",
        "vision model",
        "visual recognition",
    )
}


def load_taxonomy(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames != FIELDNAMES:
            raise ValueError(
                f"Taxonomy schema must be {FIELDNAMES!r}; found {reader.fieldnames!r}"
            )
        return list(reader)


def normalize_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def contains_term(text: str, term: str, *, case_sensitive: bool = False) -> bool:
    normalized_term = normalize_text(term.strip())
    if not normalized_term:
        return False
    pattern = re.escape(normalized_term).replace(r"\ ", r"\s+")
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.search(rf"(?<!\w){pattern}(?!\w)", text, flags) is not None


def term_matches(
    text: str,
    term: str,
    *,
    case_sensitive: bool = False,
    protect_short_language: bool = False,
) -> list[tuple[int, int]]:
    normalized_term = normalize_text(term.strip())
    if not normalized_term:
        return []
    pattern = re.escape(normalized_term).replace(r"\ ", r"\s+")
    suffix = r"(?!\w)"
    if protect_short_language and normalized_term == "C":
        suffix = r"(?![\w#+])"
    elif protect_short_language and normalized_term == "R":
        suffix = r"(?![\w&])"
    flags = 0 if case_sensitive else re.IGNORECASE
    return [
        (match.start(), match.end())
        for match in re.finditer(rf"(?<!\w){pattern}{suffix}", text, flags)
    ]


def split_terms(value: str) -> list[str]:
    return [term.strip() for term in value.split(";") if term.strip()]


def abbreviation_is_supported(text: str, abbreviation: str) -> bool:
    contexts = AMBIGUOUS_ABBREVIATION_CONTEXT.get(abbreviation.upper())
    if contexts is None:
        return True
    return any(contains_term(text, context) for context in contexts)


def skill_match_candidates(
    row: dict[str, str], text: str
) -> list[dict[str, str | int]]:
    candidates = []
    canonical = row["canonical_name"]
    canonical_case_sensitive = canonical in {"C", "R", "Go"}
    for start, end in term_matches(
        text,
        canonical,
        case_sensitive=canonical_case_sensitive,
        protect_short_language=canonical in {"C", "R"},
    ):
        candidates.append(
            {
                "skill_id": row["skill_id"],
                "canonical_name": canonical,
                "match_type": "canonical_name",
                "matched_term": canonical,
                "start": start,
                "end": end,
            }
        )

    for alias in split_terms(row["aliases"]):
        for start, end in term_matches(text, alias):
            candidates.append(
                {
                    "skill_id": row["skill_id"],
                    "canonical_name": canonical,
                    "match_type": "alias",
                    "matched_term": alias,
                    "start": start,
                    "end": end,
                }
            )

    for abbreviation in split_terms(row["abbreviation"]):
        if not abbreviation_is_supported(text, abbreviation):
            continue
        for start, end in term_matches(text, abbreviation, case_sensitive=True):
            candidates.append(
                {
                    "skill_id": row["skill_id"],
                    "canonical_name": canonical,
                    "match_type": "abbreviation",
                    "matched_term": abbreviation,
                    "start": start,
                    "end": end,
                }
            )
    return candidates


def resolve_overlaps(candidates: list[dict]) -> list[dict]:
    match_type_priority = {"canonical_name": 0, "alias": 1, "abbreviation": 2}
    candidates.sort(
        key=lambda candidate: (
            -(int(candidate["end"]) - int(candidate["start"])),
            match_type_priority[str(candidate["match_type"])],
            int(candidate["start"]),
            str(candidate["skill_id"]),
        )
    )

    accepted = []
    for candidate in candidates:
        skill_id = str(candidate["skill_id"])
        start = int(candidate["start"])
        end = int(candidate["end"])
        overlaps_longer_skill = any(
            skill_id != str(existing["skill_id"])
            and start < int(existing["end"])
            and int(existing["start"]) < end
            for existing in accepted
        )
        if overlaps_longer_skill:
            continue
        accepted.append(candidate)
    unique = {}
    for candidate in accepted:
        unique.setdefault(str(candidate["skill_id"]), candidate)
    return list(unique.values())


def extract_document_skills(rows: list[dict[str, str]], text: str) -> list[dict]:
    return resolve_overlaps([
        candidate for row in rows for candidate in skill_match_candidates(row, text)
    ])



DEFAULT_TAXONOMY = Path(__file__).resolve().parents[2] / "taxonomy" / "skills_taxonomy.csv"


def document_text(job: dict) -> str:
    """Giữ cùng vùng văn bản với recount: title thô, mô tả, yêu cầu."""
    return normalize_text("\n".join(str(job.get(field) or "") for field in TEXT_FIELDS))


class SkillExtractor:
    def __init__(self, taxonomy_path: str | Path = DEFAULT_TAXONOMY):
        self.rows = load_taxonomy(Path(taxonomy_path))
        ids = [row["skill_id"] for row in self.rows]
        names = [row["canonical_name"] for row in self.rows]
        if not self.rows or any(not value.strip() for value in ids + names):
            raise ValueError("Taxonomy phải có skill_id/canonical_name không rỗng.")
        if len(set(ids)) != len(ids) or len(set(names)) != len(names):
            raise ValueError("Taxonomy có skill_id/canonical_name bị lặp.")

    def matches(self, text: str) -> list[dict]:
        if not isinstance(text, str):
            raise TypeError("text phải là chuỗi.")
        return extract_document_skills(self.rows, normalize_text(text))

    def extract(self, text: str) -> list[str]:
        present = {match["skill_id"] for match in self.matches(text)}
        return [row["canonical_name"] for row in self.rows if row["skill_id"] in present]


def extract_skills(text: str, taxonomy_path: str | Path = DEFAULT_TAXONOMY) -> list[str]:
    return SkillExtractor(taxonomy_path).extract(text)
