from scripts.prepare_skill_gold import select_candidates


def row(job_id, text, title="Data Engineer", url=None):
    return dict(job_id=job_id, raw_job_title=title, job_description=text, source_url=url)


def test_selection_excludes_overlap_and_uses_stable_order():
    reference = [row("original", "a b c d e " * 30, url="known")]
    eligible = [row("b", "python data ingestion " * 30), row("a", "SQL query execution " * 30)]
    candidates = [row("same-url", "other text here " * 40, url="known"),
                  row("duplicate", "a b c d e " * 30),
                  row("sales", "sell goods " * 30, title="Sales Manager"), *eligible]
    selected = select_candidates(candidates, reference, 2)
    assert [r["job_id"] for r in selected] == ["a", "b"]
