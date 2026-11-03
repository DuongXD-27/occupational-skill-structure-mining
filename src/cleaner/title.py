"""
src/cleaner/title.py
QR-04: Normalize raw_job_title → normalized_job_title

Rules (from docs/data_cleaning/data_quality_rules.md §5):
- Surface cleaning ONLY. Never merge distinct roles.
- raw_job_title is immutable.
- Steps: trim → collapse spaces → strip non-title noise (salary, bonus, punctuation)
  → expand abbreviations → drop seniority level → drop explicit tech-stack suffix
  → Title Case.
- Decision 2026-10-03 (docs/decisions/integration_decisions.md §C):
  "Senior Data Analyst" → "Data Analyst". Only pure seniority levels are removed
  (Senior/Sr/Snr, Junior/Jr, Middle/Mid/Mid-level, Fresher, Entry-level).
  Lead/Principal/Head/Manager/Intern describe a role and are kept.
- Tech-stack suffix: a bracketed or delimited segment (or the words after the role
  noun) is removed only when EVERY item in it is a skill of taxonomy/skills_taxonomy.csv
  (canonical name, abbreviation or alias). Brackets with domain/role content such as
  "(CRM & Loyalty)" are kept — never strip () or [] mechanically.
- Flag AMBIGUOUS_TITLE if two distinct roles in one title.
- Flag TITLE_TOO_SHORT (<3 chars after cleaning).
- Flag TITLE_TOO_LONG (>100 chars); the title is kept whole for manual review.
- Audit flags SENIORITY_REMOVED / TECH_SUFFIX_REMOVED record what was dropped.
"""

from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Abbreviation expansions (format-only, no semantic change)
# ---------------------------------------------------------------------------

_ABBREVS = {
    r"\bSr\b\.?": "Senior",
    r"\bJr\b\.?": "Junior",
    r"\bMgr\b\.?": "Manager",
    r"\bEng\b\.?": "Engineer",
    r"\bDev\b\.?": "Developer",
    r"\bDir\b\.?": "Director",
    r"\bAssoc\b\.?": "Associate",
}

_ABBREV_COMPILED = [(re.compile(pat, re.IGNORECASE), repl) for pat, repl in _ABBREVS.items()]

# ---------------------------------------------------------------------------
# Noise patterns to strip (salary, bonus, trailing punctuation)
# ---------------------------------------------------------------------------

# Salary: "Up to 75M", "upto 1500 USD", "$2000", "2000$", "lên đến 50tr"
_SALARY_RE = re.compile(
    r"(\b(up\s*to|upto|lên\s*đến|tới)\s*\d[\d,.]*\s*(triệu|USD|VND|tr|M|K)?\b|"
    r"\$\s*\d[\d,.]*|\d[\d,.]*\s*\$)",
    re.IGNORECASE,
)

# Bonus/perk phrases
_BONUS_RE = re.compile(
    r"\s*[-–]\s*(bonus|thưởng|package|allowance|incentive)\b.*$",
    re.IGNORECASE,
)

# "English required" type trailing suffix after comma or dash
_TRAILING_SUFFIX_RE = re.compile(
    r"\s*[,\-–|]\s*(english\s+required|yêu\s+cầu\s+tiếng\s+anh|fluent\s+english).*$"
    r"|\s+(english|tiếng\s+anh(\s+tốt)?)\s*$",
    re.IGNORECASE,
)

# Recruitment noise in titles (common on TopCV): salary, experience years, workplace,
# perks, internal codes. A bracket group or a trailing " - " / "," segment made of such
# noise is dropped from normalized_job_title (raw_job_title keeps it).
_RECRUIT_NOISE_RE = re.compile(
    r"thu\s+nhập|lương|salary|\bup\s*to\b|\bupto\b|triệu|\d\s*(tr|m|k|usd|vnđ|vnd)\b|"
    r"kinh\s+nghiệm|\bkn\b|\btại\b|xe\s+đưa\s+đón|bonus|thưởng|nghỉ\s+t7|t7\s*&\s*cn|"
    r"\bid\s*\d+|quận\s*\d+|\bonsite\b|hội\s+sở|tiếng\s+anh|english|ob\s+sớm",
    re.IGNORECASE,
)


def _is_place(segment: str) -> bool:
    """Segment chỉ gồm tên địa điểm (dùng bảng location_mapping của QR-02)."""
    from .location import normalize_location  # local import: avoid cycle at module load
    parts = [p for p in re.split(r"[/,]|\bvà\b", segment) if p.strip()]
    return bool(parts) and all(normalize_location(p.strip(" ()[]"))[0] for p in parts)


def _split_top_level(text: str) -> list[str]:
    """Tách theo " - ", " – ", " | ", ", " ở cấp ngoài cùng (không cắt trong ngoặc)."""
    parts, depth, cur, i = [], 0, "", 0
    while i < len(text):
        ch = text[i]
        depth += ch in "([" ; depth -= ch in ")]"
        if depth == 0:
            m = re.match(r"\s+[-–|]\s+|,\s+", text[i:])
            if m:
                parts.append(cur)
                cur, i = "", i + m.end()
                continue
        cur += ch
        i += 1
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def _strip_recruitment_noise(text: str) -> tuple[str, bool]:
    removed = False

    def _bracket(m: re.Match) -> str:
        nonlocal removed
        inner = m.group(1)
        if _RECRUIT_NOISE_RE.search(inner) or _is_place(inner):
            removed = True
            return " "
        return m.group(0)

    text = re.sub(r"[(\[]\s*([^()\[\]]+?)\s*[)\]]", _bracket, text)
    parts = _split_top_level(text)
    if len(parts) > 1:
        keep = [parts[0]] + [p for p in parts[1:] if not (_RECRUIT_NOISE_RE.search(p) or _is_place(p))]
        if len(keep) != len(parts):
            removed = True
        text = " - ".join(keep)
    # Inline salary phrase without delimiter: "... Lương Từ 22 - 35 Triệu"
    new = re.sub(r"\s+(lương|thu\s+nhập)\b.*$", "", text, flags=re.IGNORECASE)
    if new != text and new.strip():
        text, removed = new, True
    return re.sub(r"\s{2,}", " ", text).strip(" ,-–|"), removed


# Language requirement in brackets: "(Good English)", "[Japanese N2]", "(Tiếng Anh tốt)"
_BRACKET_LANGUAGE_RE = re.compile(
    r"[(\[]\s*[^()\[\]]*\b(english|japanese|korean|chinese|tiếng\s+anh|tiếng\s+nhật|tiếng\s+hàn)\b[^()\[\]]*[)\]]",
    re.IGNORECASE,
)

# Trailing dangling punctuation: / , - | at end of string
_TRAILING_PUNCT_RE = re.compile(r"[\s/,\-–|]+$")

# Leading list numbers/bullets: "1. ", "- ", "* "
_LEADING_NOISE_RE = re.compile(r"^[\d]+\.\s*|^[-*#•]\s*")

# ---------------------------------------------------------------------------
# Seniority levels and technology suffixes
# ---------------------------------------------------------------------------

_SENIORITY_WORDS = r"(?:senior|sr\.?|snr\.?|sen|junior|jr\.?|middle|mid(?:[\s-]level)?|fresher|entry[\s-]level)"
# "Senior Data Analyst", "Sr. Data Engineer", "Junior/Middle Data Analyst"
_LEADING_SENIORITY_RE = re.compile(
    rf"^\s*{_SENIORITY_WORDS}(?:\s*[/&,-]\s*{_SENIORITY_WORDS})*\s*(?:[/&,-]\s*)?(?=\S)",
    re.IGNORECASE,
)
# "Senior/Lead Data Engineer" → "Lead Data Engineer" (lead is a role, kept)
_SENIORITY_ONLY_RE = re.compile(rf"^{_SENIORITY_WORDS}$", re.IGNORECASE)

_TAXONOMY_PATH = Path(__file__).resolve().parents[2] / "taxonomy" / "skills_taxonomy.csv"

# Role head nouns after which trailing tech words may follow ("Data Engineer Pyspark, Snowflake")
_ROLE_NOUN_RE = re.compile(
    r"\b(analyst|engineer|scientist|developer|architect|specialist|consultant|"
    r"researcher|administrator|manager|lead|expert|programmer)\b",
    re.IGNORECASE,
)
# Any role word (English or Vietnamese). A tech-suffix removal that would leave a title
# without any role word ("PowerBI (Business Intelligence)" → "PowerBI") is undone.
_ANY_ROLE_RE = re.compile(
    _ROLE_NOUN_RE.pattern[:-3] + r"|intern|developer|tester|chuyên\s+viên|kỹ\s+sư|nhân\s+viên|"
    r"trưởng\s+nhóm|trưởng\s+phòng|quản\s+lý|thực\s+tập\s+sinh|chuyên\s+gia)\b",
    re.IGNORECASE,
)
_ITEM_SPLIT_RE = re.compile(r"\s*(?:,|/|&|\||;|\band\b|\bvà\b)\s*", re.IGNORECASE)


# Taxonomy entries that name a specialisation/domain rather than a tool. A title
# segment such as "- Computer Vision" or "(LLM/RAG)" describes the role, so it is kept.
_DOMAIN_GROUPS = {
    "NLP, Vision & Multimodal AI",
    "Applied Analytics & Business Platforms",
    "Security Engineering",
}
_DOMAIN_SKILLS = {
    "Machine Learning", "Deep Learning", "Reinforcement Learning", "Recommendation Systems",
    "Statistics", "Statistical Analysis", "Generative AI", "Large Language Models",
    "Agentic AI", "AI Agents", "Multi-Agent Systems", "Retrieval-Augmented Generation",
    "Big Data", "Data Architecture",
    "Data Governance", "Data Quality", "Data Security", "Cloud Computing",
    "MLOps", "DevOps", "Distributed Systems", "Real-Time Processing", "Stream Processing",
}
# Common tools not (yet) observed in the taxonomy sample.
_EXTRA_TECH_TERMS = {
    "nosql", "t-sql", "pl/sql", "hive", "sas", "spss", "matlab", "vba", "javascript",
    "gcp", "aws", "azure", "excel", "ssis", "ssrs", "informatica", "talend", "qlik", "qlik sense",
}


@lru_cache(maxsize=4)
def load_tech_terms(path: str = str(_TAXONOMY_PATH)) -> frozenset[str]:
    """Lower-cased names of tools/technologies (taxonomy tools + a few common extras).

    Domain/specialisation entries (see _DOMAIN_GROUPS/_DOMAIN_SKILLS) are excluded.
    """
    terms: set[str] = set(_EXTRA_TECH_TERMS)
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("skill_group") in _DOMAIN_GROUPS or row.get("canonical_name") in _DOMAIN_SKILLS:
                    continue
                for key in ("canonical_name", "abbreviation"):
                    if (row.get(key) or "").strip():
                        terms.add(row[key].strip().lower())
                for alias in (row.get("aliases") or "").split(";"):
                    if alias.strip():
                        terms.add(alias.strip().lower())
    except FileNotFoundError:
        pass
    return frozenset(terms)


def _is_tech_list(segment: str, terms: frozenset[str]) -> bool:
    items = [i.strip(" .:-–") for i in _ITEM_SPLIT_RE.split(segment)]
    items = [i for i in items if i]
    return bool(items) and all(i.lower() in terms for i in items)


def _strip_tech_suffix(text: str, terms: frozenset[str]) -> tuple[str, bool]:
    """Remove explicit tech-stack segments; return (text, removed?)."""
    if not terms:
        return text, False
    new, removed = _strip_tech_suffix_raw(text, terms)
    if removed and _ANY_ROLE_RE.search(text) and not _ANY_ROLE_RE.search(new):
        return text, False
    if removed and not _ANY_ROLE_RE.search(text):
        return text, False
    return new, removed


def _strip_tech_suffix_raw(text: str, terms: frozenset[str]) -> tuple[str, bool]:
    removed = False

    # 1) Bracketed segments made only of technologies: "(SQL/Python/R)", "[Azure, Power BI]"
    def _bracket(m: re.Match) -> str:
        nonlocal removed
        if _is_tech_list(m.group(2), terms):
            removed = True
            return " "
        return m.group(0)

    text = re.sub(r"(\(|\[)\s*([^()\[\]]*?)\s*(\)|\])", _bracket, text)

    # 2) Trailing delimited segment: "Data Engineer - Spark, Kafka", "AI Engineer | LLM/RAG"
    m = re.search(r"\s+[-–|:]\s+([^-–|:]+)$", text)
    if m and _is_tech_list(m.group(1), terms):
        text, removed = text[: m.start()], True

    # 3) Words after the last role noun: "Data Engineer Pyspark, Snowflake", "Data Engineer Python/Spark"
    nouns = list(_ROLE_NOUN_RE.finditer(text))
    if nouns:
        tail = text[nouns[-1].end():]
        if tail.strip() and _is_tech_list(tail.strip(" ,"), terms):
            text, removed = text[: nouns[-1].end()], True

    return re.sub(r"\s{2,}", " ", text).strip(" ,-–|"), removed


def _strip_seniority(text: str) -> tuple[str, bool]:
    """Drop pure seniority levels at the start of the title or in a trailing bracket."""
    removed = False
    # "Senior/Lead Data Engineer": drop only the seniority part of a slash combo
    m = re.match(r"^\s*([^\s/]+)\s*/\s*(\S+)\s+", text)
    if m and _SENIORITY_ONLY_RE.match(m.group(1)) and not _SENIORITY_ONLY_RE.match(m.group(2)):
        text, removed = text[m.start(2):], True
    new = _LEADING_SENIORITY_RE.sub("", text)
    if new != text and new.strip():
        text, removed = new, True
    # "Data Analyst (Senior)", "Data Engineer (Junior/Middle)"
    def _bracket(mm: re.Match) -> str:
        nonlocal removed
        items = [i for i in re.split(r"\s*[,/&|-]\s*", mm.group(1)) if i.strip()]
        if items and all(_SENIORITY_ONLY_RE.match(i.strip()) for i in items):
            removed = True
            return " "
        return mm.group(0)
    text = re.sub(r"[(\[]\s*([^()\[\]]+?)\s*[)\]]", _bracket, text)
    # "Data Engineer Fresher", "AI Engineer Senior"
    new = re.sub(rf"\s+{_SENIORITY_WORDS}\s*$", "", text, flags=re.IGNORECASE)
    if new != text and new.strip():
        text, removed = new, True
    return re.sub(r"\s{2,}", " ", text).strip(" ,-–"), removed

# ---------------------------------------------------------------------------
# Dual-role detection
# ---------------------------------------------------------------------------

# Dual role: two different occupational tokens separated by / or |
# Allow prefix words (e.g. "Data Engineer / Data Analyst")
_DUAL_ROLE_RE = re.compile(
    r"(?:\w+\s+)*(?:analyst|engineer|scientist|developer|architect|manager|designer|"
    r"consultant|specialist|researcher)\s*[/|]\s*"
    r"(?:\w+\s+)*(?:analyst|engineer|scientist|developer|architect|manager|designer|"
    r"consultant|specialist|researcher)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Title Case helper (smarter than str.title() which uppercases after apostrophe)
# ---------------------------------------------------------------------------

_SMALL_WORDS = {"a", "an", "the", "and", "or", "but", "for", "nor",
                "on", "at", "to", "by", "of", "in", "with"}

# Tokens to keep in UPPER (well-known acronyms)
_KEEP_UPPER = {"ai", "ml", "nlp", "llm", "bi", "ux", "ui", "api",
               "sql", "etl", "elt", "qa", "ba", "hr", "sap", "erp",
               "aws", "gcp", "az", "ci", "cd", "oop"}


def _smart_title_case(text: str) -> str:
    words = text.split()
    letters = [c for c in text if c.isalpha()]
    all_caps_title = bool(letters) and all(c.isupper() for c in letters)
    result = []
    for i, word in enumerate(words):
        core = word.strip("()[]{},.;:!?&-–")
        lower_word = core.lower()
        # Short all-caps token inside a mixed-case title is an acronym: CRM, ERP, BI
        if (not all_caps_title and core.isalpha() and core.isupper() and 2 <= len(core) <= 5):
            result.append(word)
            continue
        # Preserve tokens with MEANINGFUL internal structure (C++, PyTorch, iOS)
        # but NOT simple ALL-CAPS words like "DATA" or "ANALYST"
        has_meaningful_internal = bool(re.search(r"[+]{2}|(?<=[a-z])[A-Z]|/", word))
        if has_meaningful_internal:
            result.append(word)
        elif lower_word in _KEEP_UPPER:
            result.append(word.replace(core, core.upper()))
        elif i > 0 and lower_word in _SMALL_WORDS and core == word:
            result.append(lower_word)
        else:
            result.append(_capitalize_core(word, lower_rest=all_caps_title))
    return " ".join(result)


def _capitalize_core(word: str, lower_rest: bool = True) -> str:
    """Capitalize the first letter, keep leading punctuation such as '('.

    lower_rest=False keeps the source casing of the rest (PowerBI, C&B, AI-Powered).
    """
    for idx, ch in enumerate(word):
        if ch.isalpha():
            rest = word[idx + 1:]
            return word[:idx] + ch.upper() + (rest.lower() if lower_rest else rest)
    return word


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_title(
    raw: Optional[str],
    tech_terms: Optional[frozenset[str]] = None,
) -> tuple[Optional[str], list[str]]:
    """
    Normalize raw_job_title.

    Parameters
    ----------
    raw : raw_job_title (never modified)
    tech_terms : lower-cased technology names; default = taxonomy/skills_taxonomy.csv

    Returns
    -------
    (normalized_job_title, quality_flags)
    """
    flags: list[str] = []

    if not raw or not raw.strip():
        return None, ["MISSING_JOB_TITLE"]

    terms = load_tech_terms() if tech_terms is None else tech_terms

    # Step 1: collapse whitespace (raw text may keep source line breaks)
    text = re.sub(r"\s+", " ", raw).strip()

    # Step 1b: recruitment noise (salary, years of experience, workplace, perks)
    text, noise_removed = _strip_recruitment_noise(text)
    if noise_removed:
        flags.append("RECRUITMENT_NOISE_REMOVED")

    # Step 2: strip leading list markers
    text = _LEADING_NOISE_RE.sub("", text).strip()

    # Step 3: strip salary mentions
    text = _SALARY_RE.sub("", text).strip()

    # Step 4: strip trailing bonus/perk phrases
    text = _BONUS_RE.sub("", text).strip()

    # Step 5: strip trailing language requirement suffixes
    text = _TRAILING_SUFFIX_RE.sub("", text).strip()
    text = _BRACKET_LANGUAGE_RE.sub(" ", text).strip()

    # Step 6: drop empty brackets left behind, tidy spaces inside brackets and around " / "
    text = re.sub(r"[(\[]\s*[)\]]", " ", text)
    text = re.sub(r"([(\[])\s+", r"\1", text)
    text = re.sub(r"\s+([)\]])", r"\1", text)
    text = re.sub(r"\s+/\s*|\s*/\s+", " / ", text)
    text = re.sub(r"\s{2,}", " ", text).strip()

    # Step 7: strip trailing dangling punctuation
    text = _TRAILING_PUNCT_RE.sub("", text).strip()

    # Step 8: expand abbreviations
    for pattern, repl in _ABBREV_COMPILED:
        text = pattern.sub(repl, text)

    # Step 9: drop seniority level (decision 2026-10-03)
    text, seniority_removed = _strip_seniority(text)
    if seniority_removed:
        flags.append("SENIORITY_REMOVED")

    # Step 10: drop explicit technology-stack suffix
    text, tech_removed = _strip_tech_suffix(text, terms)
    if tech_removed:
        flags.append("TECH_SUFFIX_REMOVED")
    text = _TRAILING_PUNCT_RE.sub("", text).strip()

    # Step 11: Title Case
    text = _smart_title_case(text)
    text = re.sub(r"\s{2,}", " ", text).strip()

    # --- Flags ---
    if not text or len(text) < 3:
        return text or None, flags + ["TITLE_TOO_SHORT"]

    if _DUAL_ROLE_RE.search(text):
        flags.append("AMBIGUOUS_TITLE")

    if len(text) > 100:
        flags.append("TITLE_TOO_LONG")

    return text, flags
