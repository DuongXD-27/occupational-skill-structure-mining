"""Recompute taxonomy document frequencies from the official sample corpus."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
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
EVIDENCE_FIELDNAMES = [
    "skill_id",
    "canonical_name",
    "job_id",
    "match_type",
    "matched_term",
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


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--jobs",
        type=Path,
        default=repo_root / "data" / "sample" / "sample_jobs.jsonl",
    )
    parser.add_argument(
        "--taxonomy",
        type=Path,
        default=repo_root / "taxonomy" / "skills_taxonomy_v0.1.csv",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--evidence-output", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--expected-job-count", type=int, default=45)
    parser.add_argument("--expected-source", default="ITviec")
    args = parser.parse_args()
    if args.check and args.output:
        parser.error("--check and --output cannot be used together")
    return args


def load_jobs(path: Path, expected_count: int, expected_source: str) -> list[dict]:
    jobs = []
    with path.open(encoding="utf-8-sig") as jsonl_file:
        for line_number, line in enumerate(jsonl_file, start=1):
            if not line.strip():
                continue
            try:
                job = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON on {path}:{line_number}: {error}") from error
            jobs.append(job)

    if len(jobs) != expected_count:
        raise ValueError(
            f"Expected {expected_count} jobs in {path}, found {len(jobs)}"
        )

    unexpected_sources = sorted(
        {job.get("source") for job in jobs if job.get("source") != expected_source}
    )
    if unexpected_sources:
        raise ValueError(
            f"Expected only source {expected_source!r}; found {unexpected_sources!r}"
        )

    job_ids = [job.get("job_id") for job in jobs]
    if any(not job_id for job_id in job_ids):
        raise ValueError("Every job must have a non-empty job_id")
    if len(job_ids) != len(set(job_ids)):
        raise ValueError("job_id values must be unique")
    return jobs


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


def extract_document_skills(
    rows: list[dict[str, str]], text: str
) -> list[dict[str, str | int]]:
    candidates = [
        candidate
        for row in rows
        for candidate in skill_match_candidates(row, text)
    ]
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
    matched_skill_ids = set()
    for candidate in candidates:
        skill_id = str(candidate["skill_id"])
        if skill_id in matched_skill_ids:
            continue
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
        matched_skill_ids.add(skill_id)
    return accepted


def recount(
    rows: list[dict[str, str]], jobs: list[dict]
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    documents = []
    for job in jobs:
        text = normalize_text(
            "\n".join(
                str(job.get(field) or "")
                for field in TEXT_FIELDS
                if job.get(field)
            )
        )
        documents.append((job["job_id"], text))

    counts = {row["skill_id"]: 0 for row in rows}
    evidence_rows = []
    for job_id, text in documents:
        for match in extract_document_skills(rows, text):
            skill_id = str(match["skill_id"])
            counts[skill_id] += 1
            evidence_rows.append(
                {
                    "skill_id": skill_id,
                    "canonical_name": str(match["canonical_name"]),
                    "job_id": job_id,
                    "match_type": str(match["match_type"]),
                    "matched_term": str(match["matched_term"]),
                }
            )

    recounted_rows = []
    for row in rows:
        if counts[row["skill_id"]] == 0:
            continue
        updated = dict(row)
        updated["observed_count"] = str(counts[row["skill_id"]])
        recounted_rows.append(updated)
    return recounted_rows, evidence_rows


def render_csv(rows: list[dict[str, str]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDNAMES, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def render_evidence_csv(rows: list[dict[str, str]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output, fieldnames=EVIDENCE_FIELDNAMES, lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def main() -> int:
    args = parse_args()
    try:
        jobs = load_jobs(args.jobs, args.expected_job_count, args.expected_source)
        rows = load_taxonomy(args.taxonomy)
        recounted_rows, evidence_rows = recount(rows, jobs)
        rendered = render_csv(recounted_rows)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.check:
        current = args.taxonomy.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        if current != rendered:
            print(
                "error: taxonomy observed_count values are stale; run "
                "python scripts/recount_taxonomy.py",
                file=sys.stderr,
            )
            return 1
        if args.evidence_output:
            try:
                current_evidence = args.evidence_output.read_text(
                    encoding="utf-8-sig"
                ).replace("\r\n", "\n")
            except OSError:
                current_evidence = ""
            if current_evidence != render_evidence_csv(evidence_rows):
                print(
                    "error: taxonomy evidence is stale; run python "
                    "scripts/recount_taxonomy.py --evidence-output "
                    "reports/skill_extraction/skills_taxonomy_v0.1_evidence.csv",
                    file=sys.stderr,
                )
                return 1
        print(f"Taxonomy is current for {len(jobs)} {args.expected_source} jobs.")
        return 0

    output_path = args.output or args.taxonomy
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8", newline="")
    if args.evidence_output:
        args.evidence_output.parent.mkdir(parents=True, exist_ok=True)
        args.evidence_output.write_text(
            render_evidence_csv(evidence_rows), encoding="utf-8", newline=""
        )
    print(
        f"Wrote {len(recounted_rows)} observed skills counted across "
        f"{len(jobs)} jobs to {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
