#!/usr/bin/env python3
"""
telegram/tools/generate_mcq_human_ids.py -- retrofits a deterministic,
human-readable ID onto every MCQ/descriptive question, cross-referenced
against course_catalog (2026-08-11)
--------------------------------------------------------------------------------
Pranav's ask: every question gets a NEW human-friendly ID -- ADDITIVE,
alongside its existing internal mcq_id/book_id (never replacing it) --
shaped like `CA_L2_P01_C3_U4_00876`:
    CA          course       (CA / CS / CMA)
    L2          level_num    (from course_catalog, Pranav's confirmed mapping)
    P01         paper_no     (zero-padded; course_catalog, cross-verified
                               against real cover-page sources -- see
                               populate_course_catalog.py)
    C3          chapter_no   (course_catalog, real ICAI/ICSI/ICMAI numbering)
    U4          unit_no      (course_catalog; 0 for single-unit/no-sub-unit chapters)
    00876       sequence     (5-digit, incremental, scoped per course+level+paper)

THE WHOLE POINT is synchronization: every question's chapter/unit comes
from course_catalog (the single source of truth), NEVER from the
question's own possibly-stale tag. Where a question's existing tag
disagrees with the catalog (a REAL case found 2026-08-11: CA Foundation
Quantitative Aptitude's MCQs tag themselves "U1" on every chapter, but the
real ICAI material has no sub-unit structure there at all -- the catalog
correctly says U0), the CATALOG WINS and the mismatch is reported loudly,
never silently guessed past.

IDEMPOTENT: a record that already has `human_id` is left untouched and
excluded from the "needs a new id" pool -- re-running this after adding
new questions only assigns ids to the NEW ones, continuing each subject's
sequence counter from its current max. Existing human_ids are never
renumbered, so a previously-communicated ID stays valid forever.

USAGE:
    python telegram/tools/generate_mcq_human_ids.py            # apply
    python telegram/tools/generate_mcq_human_ids.py --dry-run   # preview + mismatch report only, writes nothing
"""

import re
import sys
import json
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
import db as platform_db  # noqa: E402


def _load(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data["questions"] if isinstance(data, dict) and "questions" in data else data
    return data, records


def _save(path: Path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Per-source chapter/unit resolution -- each real content file tags itself
# a little differently (confirmed by reading all 6 files directly, not
# assumed), so each gets its own small, explicit resolver rather than one
# force-fit universal regex.
# ---------------------------------------------------------------------------
def _resolve_mcu_trust_both(record) -> tuple:
    """CA Inter Advanced Accounting -- unitcode 'M2-C7-U3' already matches
    course_catalog exactly (confirmed by direct comparison, 2026-08-11) --
    trust both chapter AND unit from the tag."""
    m = re.match(r"M\d+-C(\d+)-U(\d+)", record.get("unitcode") or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


def _resolve_mcu_trust_chapter_only(record) -> tuple:
    """CA Foundation Quantitative Aptitude -- unitcode 'M1-C1-U1' -- the
    catalog confirms chapter numbers match, but every chapter is really a
    single-unit chapter (unit_no=0) despite the tag saying 'U1' on all of
    them. Chapter trusted, unit ALWAYS forced to 0 -- flagged as a known,
    confirmed mismatch (not a per-record surprise) in the report."""
    m = re.match(r"M\d+-C(\d+)-U\d+", record.get("unitcode") or "")
    return (int(m.group(1)), 0) if m else None


def _resolve_m_chapter_only(record) -> tuple:
    """CMA Intermediate Law -- unitcode 'M12' -- chapter only, no unit
    concept in ICMAI's own material (matches catalog's unit_no=0)."""
    m = re.match(r"M(\d+)$", record.get("unitcode") or "")
    return (int(m.group(1)), 0) if m else None


def _resolve_trailing_m(record) -> tuple:
    """CMA Foundation Law -- unitcode 'CMA-FND-P1-M1' -- chapter is the
    trailing M{n}."""
    m = re.search(r"M(\d+)$", record.get("unitcode") or "")
    return (int(m.group(1)), 0) if m else None


def _normalize_chapter_name(name: str) -> str:
    """Lowercase, strip a leading article -- real, found difference
    2026-08-11: this record's own chapter_label is 'The Companies Act,
    2013' but the catalog (read verbatim off the real ToC) says just
    'Companies Act, 2013' -- a genuine, harmless naming variation, not a
    real chapter mismatch. Stripping a leading article is the fix, not
    hand-special-casing this one title."""
    name = (name or "").strip().lower()
    for article in ("the ", "a ", "an "):
        if name.startswith(article):
            name = name[len(article):]
    return name


def _resolve_by_chapter_name(record, catalog_rows) -> tuple:
    """CMA Intermediate Law descriptive -- unitcode carries no chapter
    number at all ('CMA-INT-P1-COMPANIES-ACT-2013') -- match chapter_label
    against the catalog's real chapter_name instead."""
    label = _normalize_chapter_name(record.get("chapter_label"))
    for row in catalog_rows:
        if _normalize_chapter_name(row["chapter_name"]) == label:
            return row["chapter_no"], row["unit_no"]
    return None


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


def _resolve_by_chapter_slug(record, catalog_rows) -> tuple:
    """CA Foundation Accounting / Business Economics (added 2026-08-12,
    see telegram/tools/ingest_ca_foundation_accounting_economics_mcqs.py).
    That ingestion script already set every record's chapter_slug to the
    exact slugified real course_catalog unit/chapter name -- match on
    that directly instead of re-deriving chapter/unit from a source-
    specific unitcode format (there wasn't one consistent format to
    trust; 5+ different literal shapes across the 2 source folders,
    see that script's own docstring)."""
    slug = record.get("chapter_slug")
    for row in catalog_rows:
        if _slugify(row["chapter_name"]) == slug:
            return row["chapter_no"], row["unit_no"]
    return None


# course, level, paper_no, id_field, resolver
CONTENT_SOURCES = [
    {
        "path": REPO_ROOT / "telegram" / "assets" / "exam_bot" / "mcq_questions_extracted.json",
        "course": "CA", "level": "Inter", "paper_no": "1", "id_field": "mcq_id",
        "resolve": _resolve_mcu_trust_both,
    },
    {
        "path": REPO_ROOT / "telegram" / "assets" / "exam_bot" / "book_questions_extracted.json",
        "course": "CA", "level": "Inter", "paper_no": "1", "id_field": "book_id",
        "resolve": _resolve_mcu_trust_both,
    },
    {
        "path": REPO_ROOT / "telegram" / "assets" / "exam_bot" / "ca-foundation-quantitative-aptitude" / "mcq_questions_extracted.json",
        "course": "CA", "level": "Foundation", "paper_no": "3", "id_field": "mcq_id",
        "resolve": _resolve_mcu_trust_chapter_only,
    },
    {
        "path": REPO_ROOT / "telegram" / "assets" / "faculty" / "csarunchouhan-cma-inter-law" / "cma_inter_law_faculty_mcqs.json",
        "course": "CMA", "level": "Intermediate", "paper_no": "5", "id_field": "mcq_id",
        "resolve": _resolve_m_chapter_only,
    },
    {
        "path": REPO_ROOT / "telegram" / "assets" / "faculty" / "csarunchouhan-cma-found-law" / "cma_foundation_law_faculty_mcqs.json",
        "course": "CMA", "level": "Foundation", "paper_no": "1", "id_field": "mcq_id",
        "resolve": _resolve_trailing_m,
    },
    {
        "path": REPO_ROOT / "telegram" / "assets" / "faculty" / "csarunchouhan-cma-inter-law" / "cma_inter_law_companies_act_descriptive.json",
        "course": "CMA", "level": "Intermediate", "paper_no": "5", "id_field": "book_id",
        "resolve": None,   # uses _resolve_by_chapter_name, needs catalog_rows -- wired below
    },
    {
        # Added 2026-08-12 -- see ingest_ca_foundation_accounting_economics_mcqs.py
        "path": REPO_ROOT / "telegram" / "assets" / "exam_bot" / "ca-foundation-accounting" / "mcq_questions_extracted.json",
        "course": "CA", "level": "Foundation", "paper_no": "1", "id_field": "mcq_id",
        "resolve": "by_chapter_slug",
    },
    {
        "path": REPO_ROOT / "telegram" / "assets" / "exam_bot" / "ca-foundation-business-economics" / "mcq_questions_extracted.json",
        "course": "CA", "level": "Foundation", "paper_no": "4", "id_field": "mcq_id",
        "resolve": "by_chapter_slug",
    },
]


def _format_paper(paper_no: str) -> str:
    return f"P{paper_no.zfill(2)}"


def _load_catalog(conn, course, level, paper_no) -> dict:
    """{(chapter_no, unit_no): catalog_row_dict} for one course+level+paper."""
    rows = conn.execute(
        "SELECT chapter_no, unit_no, chapter_name FROM course_catalog "
        "WHERE course=? AND level=? AND paper_no=?",
        (course, level, paper_no),
    ).fetchall()
    return {(r[0], r[1]): {"chapter_no": r[0], "unit_no": r[1], "chapter_name": r[2]} for r in rows}


def process_source(conn, src: dict, dry_run: bool) -> dict:
    path = src["path"]
    if not path.exists():
        return {"path": str(path), "skipped": "file not found"}

    data, records = _load(path)
    catalog_lookup = _load_catalog(conn, src["course"], src["level"], src["paper_no"])
    catalog_rows_list = list(catalog_lookup.values())

    level_num_row = conn.execute(
        "SELECT DISTINCT level_num FROM course_catalog WHERE course=? AND level=?",
        (src["course"], src["level"]),
    ).fetchone()
    if not level_num_row:
        return {"path": str(path), "skipped": f"no course_catalog rows for {src['course']}/{src['level']}"}
    level_num = level_num_row[0]

    already_assigned = sum(1 for r in records if r.get("human_id"))
    existing_seqs = []
    for r in records:
        hid = r.get("human_id")
        if hid:
            m = re.search(r"_(\d{5})$", hid)
            if m:
                existing_seqs.append(int(m.group(1)))
    next_seq = (max(existing_seqs) + 1) if existing_seqs else 1

    assigned, mismatches, unresolved = 0, [], []
    for r in records:
        if r.get("human_id"):
            continue   # idempotent -- never touch an already-assigned id

        if src["resolve"] == "by_chapter_slug":
            resolved = _resolve_by_chapter_slug(r, catalog_rows_list)
        elif src["resolve"] is not None:
            resolved = src["resolve"](r)
        else:
            resolved = _resolve_by_chapter_name(r, catalog_rows_list)

        if resolved is None:
            unresolved.append(r.get(src["id_field"], "<no id>"))
            continue

        chapter_no, unit_no = resolved
        catalog_hit = catalog_lookup.get((chapter_no, unit_no))
        if catalog_hit is None:
            unresolved.append(r.get(src["id_field"], "<no id>"))
            continue

        # Report (not silently skip) any case where the record's OWN raw
        # unitcode implied a different unit than the catalog-confirmed one
        # -- e.g. CA Foundation Quants' 'U1' vs the catalog's real U0.
        raw_unit_match = re.search(r"-U(\d+)$", r.get("unitcode") or "")
        if raw_unit_match and int(raw_unit_match.group(1)) != unit_no:
            mismatches.append({
                "id": r.get(src["id_field"]), "tag_said_unit": int(raw_unit_match.group(1)),
                "catalog_says_unit": unit_no, "chapter_no": chapter_no,
            })

        human_id = f"{src['course']}_L{level_num}_{_format_paper(src['paper_no'])}_C{chapter_no}_U{unit_no}_{next_seq:05d}"
        if not dry_run:
            r["human_id"] = human_id
        assigned += 1
        next_seq += 1

    if not dry_run and assigned > 0:
        _save(path, data)

    return {
        "path": str(path.relative_to(REPO_ROOT)), "total_records": len(records),
        "already_had_id": already_assigned, "newly_assigned": assigned,
        "unresolved": unresolved, "unit_mismatches": mismatches,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Preview + mismatch report only, writes nothing.")
    args = parser.parse_args()

    conn = platform_db.get_connection()
    platform_db.init_schema(conn)

    total_assigned, total_unresolved = 0, 0
    for src in CONTENT_SOURCES:
        result = process_source(conn, src, args.dry_run)
        print(f"\n{result['path'] if 'path' in result else src['path']}")
        if "skipped" in result:
            print(f"  SKIPPED: {result['skipped']}")
            continue
        print(f"  {result['total_records']} records -- {result['already_had_id']} already had a human_id, "
              f"{result['newly_assigned']} newly assigned{' (dry-run)' if args.dry_run else ''}.")
        total_assigned += result["newly_assigned"]
        if result["unit_mismatches"]:
            print(f"  {len(result['unit_mismatches'])} unit mismatch(es) between the record's own tag and "
                  f"course_catalog (catalog wins, used for the human_id):")
            for m in result["unit_mismatches"][:5]:
                print(f"    {m['id']}: tag said U{m['tag_said_unit']}, catalog says U{m['catalog_says_unit']} (chapter {m['chapter_no']})")
            if len(result["unit_mismatches"]) > 5:
                print(f"    ... and {len(result['unit_mismatches']) - 5} more")
        if result["unresolved"]:
            total_unresolved += len(result["unresolved"])
            print(f"  {len(result['unresolved'])} record(s) COULD NOT be resolved against course_catalog "
                  f"(no human_id assigned, needs manual review): {result['unresolved'][:10]}")

    print(f"\n{'='*70}")
    print(f"Total newly assigned: {total_assigned}{' (dry-run, nothing written)' if args.dry_run else ''}")
    if total_unresolved:
        print(f"Total unresolved (needs manual review): {total_unresolved}")


if __name__ == "__main__":
    main()
