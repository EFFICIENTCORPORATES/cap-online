"""
QA diff: does the merged QUESTION-BANK-BOOK.html actually match what
questions_index.json says should be in it?

For every questions_index.json row that generate_chapter_book.select_chapter_rows()
says belongs in some chapter's Descriptive or Integrated section, this script:
  1. Regenerates that exact row's qblock HTML via the real
     generate_chapter_book.render_qblock() (the same function that built the book),
  2. Parses that regenerated HTML with extract_book_questions.parse_qblock()
     (the same parser used on the real book),
  3. Looks for a matching qblock actually present in the merged book (parsed
     fresh via extract_book_questions.extract_book()),
  4. Field-by-field compares the two.

No label-formatting or field logic is re-derived here -- both sides go
through the exact same render_qblock()/parse_qblock() functions the real
pipeline uses, so a diff here means a REAL drift between the data and the
published book, not a false positive from two independently-written
parsers disagreeing with each other.

Three outcomes per expected row:
  - MISSING   : expected in the book, not found there at all (dropped question)
  - DRIFTED   : found, but one or more fields differ from what the data says
                (stale regeneration, hand-edit that didn't flow back, etc.)
  - (silent)  : found and every compared field matches -- not reported

Plus, the reverse direction:
  - ORPHAN    : a qblock physically present in the book with no matching
                expected row at all (stale leftover content, e.g. from an
                unitcode/CHAPTERS renumbering)

Usage:  python diff_book_vs_index.py
Output: first_run/output/qa/book-vs-index-diff.json
        first_run/output/qa/book-vs-index-diff.md
"""
import json
import os
import re
import sys
from collections import defaultdict
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.normpath(os.path.join(HERE, "..", "output"))
QA_DIR = os.path.join(OUTPUT_DIR, "qa")
DIFF_JSON_PATH = os.path.join(QA_DIR, "book-vs-index-diff.json")
DIFF_MD_PATH = os.path.join(QA_DIR, "book-vs-index-diff.md")

sys.path.insert(0, HERE)
from qb_merge import CHAPTERS  # noqa: E402
from generate_chapter_book import load_index, select_chapter_rows, render_qblock  # noqa: E402
from extract_book_questions import parse_qblock, extract_book, BOOK_PATH  # noqa: E402

# Fields compared between the expected (regenerated) qblock and the actual
# (found-in-book) qblock. book_id is excluded deliberately -- it's a
# positional per-chapter serial number (chapter_slug-NNN), not stable content,
# so a shuffle in row order would flag every single row as "drifted" on that
# field alone without indicating any real problem.
COMPARE_FIELDS = [
    "flagged", "marks_text", "approx_time_text", "topic_text", "badges",
    "question_html", "answer_html", "answer_letter", "mistake_type", "mistake_text",
]


def _normalize(value):
    """Collapse whitespace for the two *_html fields so trivial
    serialization differences (newlines, repeated spaces) don't register as
    drift; everything else is compared as-is."""
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    return value


def build_expected():
    """One entry per (chapter, section, row) questions_index.json says should
    render into the book -- mirrors exactly what generate_all_chapter_books.py
    would produce, via the same select_chapter_rows() helper."""
    data = load_index()
    expected = []
    for slug, _filename, chapter_label, unitcode in CHAPTERS:
        _home, descriptive, integrated = select_chapter_rows(data, unitcode)
        for section, rows in (("descriptive", descriptive), ("integrated", integrated)):
            for row in rows:
                qblock_html = render_qblock(row, 0, unitcode.replace("-", ""))
                tag = BeautifulSoup(qblock_html, "html.parser").find("div", class_="qblock")
                fields = parse_qblock(tag)
                key = (slug, section, fields["src_text"], fields["qno_text"])
                expected.append({
                    "key": key,
                    "chapter_slug": slug,
                    "chapter_label": chapter_label,
                    "unitcode": unitcode,
                    "section": section,
                    "source_row_id": row.get("id"),
                    "fields": fields,
                })
    return expected


def build_actual():
    all_rows, per_chapter_counts, missing_sections = extract_book(BOOK_PATH, verbose=False)
    actual_by_key = defaultdict(list)
    for row in all_rows:
        key = (row["chapter_slug"], row["section"], row["src_text"], row["qno_text"])
        actual_by_key[key].append(row)
    return actual_by_key, all_rows, missing_sections


def diff_fields(expected_fields, actual_fields):
    diffs = []
    for f in COMPARE_FIELDS:
        e = _normalize(expected_fields.get(f))
        a = _normalize(actual_fields.get(f))
        if e != a:
            diffs.append({"field": f, "expected": e, "actual": a})
    return diffs


def main():
    expected = build_expected()
    actual_by_key, all_actual_rows, missing_sections = build_actual()

    matched_keys = set()
    missing = []
    drifted = []
    ambiguous = []

    for exp in expected:
        candidates = actual_by_key.get(exp["key"], [])
        if not candidates:
            missing.append(exp)
            continue
        if len(candidates) > 1:
            ambiguous.append({**exp, "candidate_count": len(candidates)})
        actual = candidates[0]
        matched_keys.add(exp["key"])
        diffs = diff_fields(exp["fields"], actual)
        if diffs:
            drifted.append({
                "key": list(exp["key"]),
                "chapter_slug": exp["chapter_slug"],
                "chapter_label": exp["chapter_label"],
                "section": exp["section"],
                "source_row_id": exp["source_row_id"],
                "book_id": actual.get("book_id"),
                "diffs": diffs,
            })

    orphans = []
    for key, rows in actual_by_key.items():
        if key not in matched_keys:
            for row in rows:
                orphans.append(row)

    total_expected = len(expected)
    total_actual = len(all_actual_rows)
    total_matched = len(matched_keys)

    report = {
        "book_path": os.path.relpath(BOOK_PATH, OUTPUT_DIR),
        "totals": {
            "expected_rows": total_expected,
            "actual_rows_in_book": total_actual,
            "matched": total_matched,
            "missing": len(missing),
            "drifted": len(drifted),
            "orphan": len(orphans),
            "ambiguous_keys": len(ambiguous),
        },
        "missing_chapter_sections": missing_sections,
        "missing": [
            {
                "chapter_slug": m["chapter_slug"], "chapter_label": m["chapter_label"],
                "section": m["section"], "source_row_id": m["source_row_id"],
                "src_text": m["fields"]["src_text"], "qno_text": m["fields"]["qno_text"],
            }
            for m in missing
        ],
        "drifted": drifted,
        "orphan": [
            {
                "chapter_slug": o["chapter_slug"], "section": o["section"],
                "book_id": o["book_id"], "src_text": o["src_text"], "qno_text": o["qno_text"],
            }
            for o in orphans
        ],
        "ambiguous_keys": [
            {"key": list(a["key"]), "candidate_count": a["candidate_count"]}
            for a in ambiguous
        ],
    }

    os.makedirs(QA_DIR, exist_ok=True)
    with open(DIFF_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    write_markdown_report(report)

    print(f"Expected {total_expected} rows, found {total_actual} rows in the book, "
          f"{total_matched} matched.")
    print(f"  Missing:   {len(missing)}")
    print(f"  Drifted:   {len(drifted)}")
    print(f"  Orphan:    {len(orphans)}")
    print(f"  Ambiguous: {len(ambiguous)}")
    print(f"\nWrote {DIFF_JSON_PATH}")
    print(f"Wrote {DIFF_MD_PATH}")


def write_markdown_report(report):
    t = report["totals"]
    lines = [
        "# Question Bank Book vs. questions_index.json — QA Diff",
        "",
        f"Book: `{report['book_path']}`",
        "",
        f"- Expected (from questions_index.json via select_chapter_rows): **{t['expected_rows']}**",
        f"- Actually found in the book: **{t['actual_rows_in_book']}**",
        f"- Matched: **{t['matched']}**",
        f"- Missing: **{t['missing']}**",
        f"- Drifted: **{t['drifted']}**",
        f"- Orphan: **{t['orphan']}**",
        f"- Ambiguous keys (2+ candidates): **{t['ambiguous_keys']}**",
        "",
    ]

    if report["missing_chapter_sections"]:
        lines.append("## Chapter sections entirely missing from the book")
        lines.append("")
        for s in report["missing_chapter_sections"]:
            lines.append(f"- `{s}`")
        lines.append("")

    if report["missing"]:
        lines.append("## Missing (expected in book, not found)")
        lines.append("")
        for m in report["missing"]:
            lines.append(f"- **{m['chapter_slug']}** / {m['section']} — "
                          f"{m['src_text']} · {m['qno_text']} (row id `{m['source_row_id']}`)")
        lines.append("")

    if report["drifted"]:
        lines.append("## Drifted (found, but fields differ)")
        lines.append("")
        for d in report["drifted"]:
            lines.append(f"- **{d['chapter_slug']}** / {d['section']} — "
                          f"{d['key'][2]} · {d['key'][3]} (row id `{d['source_row_id']}`, "
                          f"book id `{d['book_id']}`)")
            for fd in d["diffs"]:
                exp_s = str(fd["expected"])
                act_s = str(fd["actual"])
                if len(exp_s) > 200:
                    exp_s = exp_s[:200] + "…"
                if len(act_s) > 200:
                    act_s = act_s[:200] + "…"
                lines.append(f"    - `{fd['field']}`: expected `{exp_s}` vs actual `{act_s}`")
        lines.append("")

    if report["orphan"]:
        lines.append("## Orphan (in the book, no matching expected row)")
        lines.append("")
        for o in report["orphan"]:
            lines.append(f"- **{o['chapter_slug']}** / {o['section']} — "
                          f"{o['src_text']} · {o['qno_text']} (book id `{o['book_id']}`)")
        lines.append("")

    if report["ambiguous_keys"]:
        lines.append("## Ambiguous keys (2+ actual qblocks share the same match key)")
        lines.append("")
        for a in report["ambiguous_keys"]:
            lines.append(f"- `{a['key']}` — {a['candidate_count']} candidates")
        lines.append("")

    if not (report["missing"] or report["drifted"] or report["orphan"] or
            report["ambiguous_keys"] or report["missing_chapter_sections"]):
        lines.append("**No discrepancies found.** The book matches questions_index.json exactly.")
        lines.append("")

    with open(DIFF_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
